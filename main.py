import re
import os

def build_map_block(class_name, project_directory):
    if class_name == "Long":
        return ".map((row, rowMetadata) -> row.get(\"id\", Long.class))"

    if class_name == "String":
        return ".map((row, rowMetadata) -> row.get(0, String.class))"

    properties = []

    # Percorrer os arquivos do diretório do projeto
    for subdir, dirs, files in os.walk(project_directory):
        for file_name in files:
            if file_name.endswith('.java'):
                file_path = os.path.join(subdir, file_name)
                with open(file_path, 'r') as file_content:
                    content = file_content.read()
                    # Procurar pela classe e obter suas propriedades e tipos
                    if f'class {class_name} ' in content or f'class {class_name}<' in content:
                        class_lines = content.split('\n')
                        for line in class_lines:
                            line = line.strip()
                            # Você pode ajustar essa lógica para extrair propriedades e tipos com base em suas convenções
                            if line.startswith('private') and '(' not in line:
                                type_and_name = line.split(' ')[1:3]
                                prop_type = type_and_name[0]
                                prop_name = type_and_name[1].replace(';', '')
                                properties.append((prop_name, prop_type))
                        break

    map_block = f".map((row, rowMetaData) -> {class_name}.builder()\n"
    for prop, prop_type in properties:
        map_block += f'    .{prop}(row.get("{camel_to_snake(prop)}", {prop_type}.class))\n'
    map_block += "    .build())"
    return map_block

def camel_to_snake(name):
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def process_file(methods_to_process, path_to_scripts):
    print("Iniciando atualização...")
    with open(path_to_scripts, 'r') as file:
        content = file.read()
    print("Arquivo aberto")

    # Substituir .execute por .sql, remover .as() e substituir .fetch() pelo mapeamento definido no build_map_block
    for method in methods_to_process:
        method_name = method["Metodo"]
        retorno = method["Retorno"]

        execute_pattern = fr'(\b{method_name}\s*\(.*?\)\s*\{{.*?)(\.execute\()'
        content = re.sub(execute_pattern, fr'\1.sql(', content, flags=re.DOTALL)

        as_pattern = fr'(\b{method_name}\s*\(.*?\)\s*\{{.*?)(\.as\([A-Za-z<>,\s]*\.class\))'
        content = re.sub(as_pattern, fr'\1', content, flags=re.DOTALL)

        if retorno and retorno != "Void":
            fetch_pattern = fr'(\b{method_name}\s*\(.*?\)\s*\{{.*?)(\.fetch\(\))'
            map_block = build_map_block(retorno, '/home/leonardo/Documents/Projetos/Dimed/coupon-service/')
            content = re.sub(fetch_pattern, fr'\1\n{map_block}', content, flags=re.DOTALL)

    with open(path_to_scripts, 'w') as file:
        file.write(content)

    print("Atualização concluída!")

# Lista de métodos e retornos que você deseja processar
methods_to_process = [
    {"Metodo": "saveLog", "Retorno": "CouponLogEntity"},
    {"Metodo": "findPaginatedCouponLog", "Retorno": "CouponLogEntity"},
    {"Metodo": "findPaginatedCouponLog", "Retorno": "CouponLogEntity"},
    # Adicione mais métodos e retornos conforme necessário
]

# Caminho para o arquivo que você deseja testar
path_to_scripts = '/home/leonardo/Documents/Projetos/Dimed/coupon-service/impl/src/main/java/br/com/dimed/couponservice/impl/subsidiary/SubsidiaryCustomRepositoryImpl.java'
# Chame a função diretamente com a lista de métodos e o caminho do arquivo que você deseja testar
process_file(methods_to_process, path_to_scripts)
