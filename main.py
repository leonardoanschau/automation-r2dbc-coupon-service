import re
import os

def build_map_block(class_name, project_directory):
    if class_name == "Long":
        return ".map((row, rowMetadata) -> row.get(\"id\", Long.class))"
    if class_name == "String":
        return ".map((row, rowMetadata) -> row.get(0, String.class))"

    properties = get_properties_for_class(class_name, project_directory)
    map_block = f".map((row, rowMetaData) -> {class_name}.builder()\n"
    for prop, prop_type in properties:
        map_block += f'    .{prop}(row.get("{camel_to_snake(prop)}", {prop_type}.class))\n'
    map_block += "    .build())"
    return map_block

def build_mapping_method(class_name, properties):
    method_name = f"MAPPING_{camel_to_snake(class_name).upper()}"
    mapping_method = f"public static final BiFunction<Row, RowMetadata, {class_name}> {method_name} =\n"
    mapping_method += f"    (row, rowMetaData) -> {class_name}.builder()\n"
    for prop, prop_type in properties:
        mapping_method += f'        .{prop}(row.get("{camel_to_snake(prop)}", {prop_type}.class))\n'
    mapping_method += "        .build();"
    return mapping_method

def get_properties_for_class(class_name, project_directory):
    properties = []
    for subdir, dirs, files in os.walk(project_directory):
        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(subdir, file_name)
                with open(file_path, 'r') as file_content:
                    content = file_content.read()
                    if f'class {class_name} ' in content or f'class {class_name}<' in content:
                        class_lines = content.split('\n')
                        for line in class_lines:
                            line = line.strip()
                            if line.startswith('private') and '(' not in line:
                                type_and_name = line.split(' ')[1:3]
                                prop_type = type_and_name[0]
                                prop_name = type_and_name[1].replace(';', '')
                                properties.append((prop_name, prop_type))
                        break
    return properties

def camel_to_snake(name):
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def process_file(methods_to_process, path_to_scripts):
    print("Iniciando atualização...")
    with open(path_to_scripts, 'r') as file:
        content = file.read()
    print("Arquivo aberto")

    for method in methods_to_process:
        method_name = method["Metodo"]
        retorno = method["Retorno"]
        map_object = method["MapearObjeto"]

        execute_pattern = fr'(\b{method_name}\s*\(.*?\)\s*\{{.*?)(\.execute\()'
        content = re.sub(execute_pattern, fr'\1.sql(', content, flags=re.DOTALL)

        as_pattern = fr'(\b{method_name}\s*\(.*?\)\s*\{{.*?)(\.as\([A-Za-z<>,\s]*\.class\))'
        content = re.sub(as_pattern, fr'\1', content, flags=re.DOTALL)

        if retorno and retorno != "Void":
            fetch_pattern = fr'(\b{method_name}\s*\(.*?\)\s*\{{.*?)(\.fetch\(\))'
            mapping_function_name = f"MAPPING_{camel_to_snake(retorno).upper()}"

            if map_object:
                if mapping_function_name not in content:
                    properties = get_properties_for_class(retorno, '/home/leonardo/Documents/Projetos/Dimed/coupon-service/')
                    mapping_method = build_mapping_method(retorno, properties)
                    content += f"\n{mapping_method}\n"
                map_block = f'.map({mapping_function_name})'
            else:
                map_block = build_map_block(retorno, '/home/leonardo/Documents/Projetos/Dimed/coupon-service/')
            
            content = re.sub(fetch_pattern, fr'\1\n{map_block}', content, flags=re.DOTALL)

    with open(path_to_scripts, 'w') as file:
        file.write(content)

    print("Atualização concluída!")

methods_to_process = [
    {"Metodo": "getCouponsForExport", "Retorno": "ExportCouponModel", "MapearObjeto": True},
    # Adicione mais métodos e retornos conforme necessário
]

path_to_scripts = '/home/leonardo/Documents/Projetos/Dimed/coupon-service/impl/src/main/java/br/com/dimed/couponservice/impl/export/ExportCustomRepositoryImpl.java' 

process_file(methods_to_process, path_to_scripts)
