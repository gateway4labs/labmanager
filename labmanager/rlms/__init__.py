# 
# Add the proper managers by pointing to a module
# 

RLMSS = {
    # "RLMS type" : {
    #     "version" : "full.module.path",
    # },
    "WebLab-Deusto" : {
        "4.0" : 'labmanager.rlms.weblabdeusto',
    },
    "iLab" : {
        "4.5" : 'labmanager.rlms.ilab',
    },
}

def get_supported_types():
    return RLMSS.keys()
        
def get_supported_versions(rlms_type):
    if rlms_type in RLMSS:
        return RLMSS[rlms_type].keys()
    return []

def is_supported(rlms_type, rlms_version):
    module_name = RLMSS.get(rlms_type, {}).get(rlms_version, None)
    return module_name is not None

def get_module(rlms_type, rlms_version):
    module_name = RLMSS.get(rlms_type, {}).get(rlms_version, None)
    if module_name is None: 
        raise Exception("Misconfiguration: %s %s does not exist" % (rlms_type, rlms_version))

    return __import__(module_name, {}, {}, [ module_name ])

def get_form_class(rlms_type, rlms_version):
    module = get_module(rlms_type, rlms_version)
    return module.AddForm

def get_permissions_form_class(rlms_type, rlms_version):
    module = get_module(rlms_type, rlms_version)
    return module.PermissionForm

def get_connetion_tester(rlms_type, rlms_version):
    module = get_module(rlms_type, rlms_version)
    return module.connection_tester

def get_manager_class(rlms_type, rlms_version):
    module = get_module(rlms_type, rlms_version)
    return module.ManagerClass
