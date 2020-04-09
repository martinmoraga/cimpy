import logging
import cimpy
import xmltodict
import os
import pytest_check as check

logging.basicConfig(filename='Test_export_with_imported_files.log', level=logging.INFO, filemode='w')

short_profile_name = {
    "DiagramLayout": 'DI',
    "Dynamics": "DY",
    "Equipment": "EQ",
    "GeographicalLocation": "GL",
    "StateVariables": "SV",
    "SteadyStateHypothesis": "SSH",
    "Topology": "TP"
}

example_path = os.path.join('..',
                            os.path.join('examples',
                                         os.path.join('sampledata',
                                                      os.path.join('CIGRE_MV',
                                                                   'CIGRE_MV_Rudion_With_LoadFlow_Results'))))


# This test function tests the export functionality by comparing files before the import and export procedure with the
# exported files. Since cyclic attributes are not resolved in this package, the imported files only need to be a subset
# of the exported files.
def test_export_with_imported_files():
    import_files = [os.path.join(example_path, 'Rootnet_FULL_NE_24J13h_DI.xml'),
                    os.path.join(example_path, 'Rootnet_FULL_NE_24J13h_EQ.xml'),
                    os.path.join(example_path, 'Rootnet_FULL_NE_24J13h_SV.xml'),
                    os.path.join(example_path, 'Rootnet_FULL_NE_24J13h_TP.xml'), ]

    activeProfileList = ['DI', 'EQ', 'SV', 'TP']

    imported_files, namespaces, url_reference_dict = cimpy.cim_import(import_files, 'cgmes_v2_4_15')
    cimpy.cim_export(imported_files, namespaces, 'EXPORTED_Test', 'cgmes_v2_4_15',
                     activeProfileList, url_reference_dict)

    test_list = []
    for file in import_files:
        xmlstring = open(file, encoding='utf8').read()
        parsed_export_file = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)
        test_list.append(parsed_export_file['rdf:RDF'])

    export_list = []
    for file in os.listdir(os.getcwd()):
        if file.endswith(".xml") and 'EXPORTED' in str(file):
            xmlstring = open(file, encoding='utf8').read()
            parsed_export_file = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)
            export_list.append(parsed_export_file['rdf:RDF'])

    export_dict = {}
    for export_file in export_list:
        profile = export_file['md:FullModel']['md:Model.profile']
        for key in short_profile_name.keys():
            if key in profile:
                export_dict[key] = export_file

    test_dict = {}
    for elem in test_list:
        profile = elem['md:FullModel']['md:Model.profile']
        for key in short_profile_name.keys():
            if key in profile:
                test_dict[key] = elem

    for profile, current_test_dict in test_dict.items():
        check.is_in(profile, export_dict.keys())
        if profile in export_dict.keys():
            current_export_dict = export_dict[profile]
            for class_key in current_test_dict:
                if 'cim:' not in class_key or class_key in ['cim:NameType', 'cim:Name']:
                    continue
                check.is_in(class_key, current_export_dict.keys())
                if class_key in current_export_dict.keys():
                    current_export_class = current_export_dict[class_key]
                    current_test_class = current_test_dict[class_key]
                    test_mRIDs = []
                    test_class_dict = {}
                    if isinstance(current_test_class, list):
                        for obj in current_test_class:
                            try:
                                test_mRIDs.append(obj['$rdf:ID'])
                                test_class_dict[obj['$rdf:ID']] = obj
                            except KeyError:
                                try:
                                    test_mRIDs.append(obj['$rdf:about'])
                                    test_class_dict[obj['$rdf:about']] = obj
                                except KeyError:
                                    check.is_in('$rdf:about', obj.keys())
                                    check.is_in('$rdf:ID', obj.keys())
                    else:
                        try:
                            test_mRIDs.append(current_test_class['$rdf:ID'])
                            test_class_dict[current_test_class['$rdf:ID']] = current_test_class
                        except KeyError:
                            try:
                                test_mRIDs.append(current_test_class['$rdf:about'])
                                test_class_dict[current_test_class['$rdf:about']] = obj
                            except KeyError:
                                check.is_in('$rdf:about', current_test_class.keys())
                                check.is_in('$rdf:ID', current_test_class.keys())

                    export_mRIDs = []
                    export_class_dict = {}
                    if isinstance(current_export_class, list):
                        for obj in current_export_class:
                            try:
                                export_mRIDs.append(obj['$rdf:ID'])
                                export_class_dict[obj['$rdf:ID']] = obj
                            except KeyError:
                                try:
                                    export_mRIDs.append(obj['$rdf:about'])
                                    export_class_dict[obj['$rdf:about']] = obj
                                except KeyError:
                                    check.is_in('$rdf:about', obj.keys())
                                    check.is_in('$rdf:ID', obj.keys())
                    else:
                        try:
                            export_mRIDs.append(current_export_class['$rdf:ID'])
                            export_class_dict[current_export_class['$rdf:ID']] = current_export_class
                        except KeyError:
                            try:
                                export_mRIDs.append(current_export_class['$rdf:about'])
                                export_class_dict[current_export_class['$rdf:about']] = obj
                            except KeyError:
                                check.is_in('$rdf:about', current_export_class.keys())
                                check.is_in('$rdf:ID', current_export_class.keys())

                    for mRID in test_mRIDs:
                        check.is_in(mRID, export_mRIDs)
                        if mRID in export_mRIDs:
                            test_attr = test_class_dict[mRID].items()
                            export_attr = export_class_dict[mRID].items()
                            for item in test_attr:
                                if item[0] in ['cim:NameType', 'cim:ExternalNetworkInjection.referencePriority',
                                               'cim:Terminal.connected']:
                                    continue
                                elif item[0] == 'cim:Terminal.sequenceNumber':
                                    test_item = 'cim:ACDCTerminal.sequenceNumber'
                                else:
                                    test_item = item[0]

                                if item[1] in ['0', '0e+000', '0.0', '', 'false', 'None', 'list',
                                               {'$rdf:resource': '#_32d6d32e-c3f0-43d4-8103-079a15594fc6'}]:
                                    continue
                                if isinstance(item[1], dict):
                                    test_item = item
                                elif len(item[1].split('.')) > 1:
                                    try:
                                        test_item = (item[0], str(float(item[1])))
                                    except ValueError:
                                        continue
                                    except TypeError:
                                        pass
                                elif item[1] == 'true':
                                    test_item = (test_item, 'True')
                                else:
                                    test_item = (test_item, item[1])

                                check.is_in(test_item, export_attr)

    for file in os.listdir(os.getcwd()):
        if 'EXPORTED' in str(file):
            os.remove(file)