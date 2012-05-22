# 
# Add the proper managers by pointing to a class path
# 

RLMSS = {
    # "RLMS type" : {
    #     "version" : "full.class.path",
    # },
    "WebLab-Deusto" : {
        "4.0" : 'labmanager.rlms.weblabdeusto.WebLabDeustoManager',
    },
    "iLab" : {
        "4.5" : 'labmanager.rlms.ilab.ILabManager',
    },
}

def get_supported_types():
    return RLMSS.keys()
        
def get_supported_versions(rlms_type):
    if rlms_type in RLMSS:
        return RLMSS[rlms_type].keys()
    return []

def get_manager(rlms_type, rlms_version):
    pass # TODO

