import sys
from pathlib import Path
from ihp import PDK

# Add the folder containing extractor.py to Python path
sys.path.append("/Users/delficomerso/Desktop/gsim/src")

# Now import the function
from gsim.common.stack.extractor import extract_from_pdk

# Activate IHP PDK
PDK.activate()

# Extract the LayerStack YAML
stack = extract_from_pdk(
    PDK,
    output_path=Path("/Users/delficomerso/Desktop/IHP/ihp/s_parameters/ihp_stack.yaml"),
    include_substrate=True,
    air_above=400.0,          
)

# Validate stack
print(stack.validate_stack())

