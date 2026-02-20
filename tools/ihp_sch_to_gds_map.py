import os
import ast
import yaml
from pprint import pprint
from difflib import SequenceMatcher

# --- CONFIG ---

IHPS_DIRS = ["ihp/cells", "ihp/cells2"]  # Prioritize cells (which has more complete layer specs)
YAML_FILE = "ihp_sch_param_descriptions.yml"
MAPPING_FILE = "ihp_to_gds_mapping.yml"
SIMILARITY_THRESHOLD = 0.5  # Minimum similarity score (0-1)


# --- FUNCTIONS ---


def load_yaml_descriptions(yaml_file):
    """Load argument descriptions from YAML."""
    with open(yaml_file) as f:
        return yaml.safe_load(f)


def extract_pcell_args(py_file):
    """Extract function arguments and defaults from @gf.cell decorated functions."""
    with open(py_file) as f:
        tree = ast.parse(f.read(), filename=py_file)

    pcells = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check if function has @gf.cell decorator
            has_gf_cell = any(
                (isinstance(dec, ast.Attribute) and dec.attr == "cell") or
                (isinstance(dec, ast.Name) and dec.id == "cell")
                for dec in node.decorator_list
            )
            if has_gf_cell:
                args_with_defaults = {}
                # Get function arguments and their defaults
                num_defaults = len(node.args.defaults)
                args_list = node.args.args  # Don't skip - @gf.cell functions don't have 'self'
                num_args = len(args_list)
                
                for i, arg in enumerate(args_list):
                    # Get default value if exists
                    default_idx = i - (num_args - num_defaults)
                    if default_idx >= 0:
                        default_node = node.args.defaults[default_idx]
                        # Try to extract the default value
                        if isinstance(default_node, ast.Constant):
                            args_with_defaults[arg.arg] = default_node.value
                        else:
                            args_with_defaults[arg.arg] = None
                    else:
                        args_with_defaults[arg.arg] = None
                
                pcells[node.name] = args_with_defaults
    return pcells


def map_pcell_to_gds(pcell_args_with_defaults, descriptions):
    """
    Map @gf.cell function arguments to schematic descriptions.
    - Output all arguments from @gf.cell
    - Try exact match, then case-insensitive match
    - For non-layer args: also try fuzzy matching on descriptions
    - For layer_* args: only exact/case-insensitive, NO fuzzy matching
    - Otherwise use the default value from @gf.cell
    """
    mapping = {}
    
    def similarity(s1, s2):
        """Calculate similarity score between two strings (0-1)."""
        return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()
    
    # For each @gf.cell argument, try to find a matching schematic description
    for pcell_arg, default_val in pcell_args_with_defaults.items():
        matched_desc_key = None
        best_similarity = 0
        
        # Try exact match first
        if pcell_arg in descriptions:
            matched_desc_key = pcell_arg
        else:
            # Try case-insensitive exact match
            for desc_key in descriptions.keys():
                if desc_key.lower() == pcell_arg.lower():
                    matched_desc_key = desc_key
                    break
        
        # For non-layer arguments, try fuzzy matching on description values
        if not matched_desc_key and not pcell_arg.startswith("layer_"):
            for desc_key, desc_value in descriptions.items():
                # Match against description values (not keys) - more semantic
                value_sim = similarity(pcell_arg, desc_value)
                
                if value_sim > best_similarity and value_sim >= SIMILARITY_THRESHOLD:
                    best_similarity = value_sim
                    matched_desc_key = desc_key
        
        # If matched, map to description key; otherwise use default
        mapping[pcell_arg] = matched_desc_key if matched_desc_key else default_val

    return mapping


def save_mapping(mapping, filename=MAPPING_FILE):
    """Save mapping to YAML file."""
    with open(filename, "w") as f:
        yaml.dump(mapping, f)
    print(f"Mapping saved to {filename}")


# --- MAIN ---


def main():
    # 1. Load YAML descriptions
    descriptions = load_yaml_descriptions("ihp_sch_param_descriptions.yml")

    # 2. Extract all PCell arguments (keep first version found, but process in sorted order)
    all_pcell_args = {}
    for dir_path in IHPS_DIRS:
        if not os.path.exists(dir_path):
            continue
        for filename in sorted(os.listdir(dir_path)):  # Sort for consistent ordering
            if filename.endswith(".py") and filename != "fixed.py":  # Skip fixed.py
                pcells = extract_pcell_args(os.path.join(dir_path, filename))
                for name, args in pcells.items():
                    # Keep the first version found (from higher priority directory)
                    if name not in all_pcell_args:
                        all_pcell_args[name] = args

    # 3. Map PCell args to schematic descriptions
    gds_mapping = {}
    for comp_name in all_pcell_args.keys():
        comp_descriptions = descriptions.get(comp_name, {})
        gds_mapping[comp_name] = map_pcell_to_gds(all_pcell_args[comp_name], comp_descriptions)

    # 4. Print and save
    pprint(gds_mapping)
    save_mapping(gds_mapping)


if __name__ == "__main__":
    main()
