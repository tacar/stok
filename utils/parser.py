#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Swift と Kotlin のコードを解析するためのパーサーユーティリティ
"""

import re
from typing import Dict, List, Tuple, Optional, Any

def parse_swift_file(content: str) -> Dict[str, Any]:
    """
    Swift ファイルの内容を解析します。

    Args:
        content: Swift ファイルの内容

    Returns:
        解析結果を含む辞書
    """
    result = {
        'imports': [],
        'class_name': None,
        'superclass': None,
        'protocols': [],
        'properties': [],
        'methods': [],
        'is_struct': False,
        'is_class': False,
        'is_enum': False,
        'is_protocol': False,
        'is_extension': False,
        'is_viewmodel': False,
        'is_view': False,
        'is_model': False,
        'is_repository': False,
        'is_service': False,
        'uses_combine': False,
        'uses_swiftdata': False,
        'uses_firebase': False,
    }

    # インポートを抽出
    import_pattern = r'import\s+(\w+)'
    result['imports'] = re.findall(import_pattern, content)

    # クラス/構造体/列挙型/プロトコル/拡張の定義を抽出
    class_pattern = r'(class|struct|enum|protocol|extension)\s+(\w+)(?:\s*:\s*([^{]+))?'
    class_matches = re.findall(class_pattern, content)

    if class_matches:
        type_name, name, inheritance = class_matches[0]
        result['class_name'] = name.strip()

        if type_name == 'class':
            result['is_class'] = True
        elif type_name == 'struct':
            result['is_struct'] = True
        elif type_name == 'enum':
            result['is_enum'] = True
        elif type_name == 'protocol':
            result['is_protocol'] = True
        elif type_name == 'extension':
            result['is_extension'] = True

        # 継承関係を解析
        if inheritance:
            inheritance_parts = [part.strip() for part in inheritance.split(',')]
            if inheritance_parts:
                result['superclass'] = inheritance_parts[0]
                result['protocols'] = inheritance_parts[1:]

    # プロパティを抽出
    property_pattern = r'(?:var|let)\s+(\w+)\s*:\s*([^\n{]+)'
    property_matches = re.findall(property_pattern, content)

    for name, type_info in property_matches:
        result['properties'].append({
            'name': name,
            'type': type_info.strip(),
            'is_published': '@Published' in type_info or '@State' in type_info or '@Binding' in type_info,
        })

    # メソッドを抽出
    method_pattern = r'func\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*([^{]+))?'
    method_matches = re.findall(method_pattern, content)

    for name, params, return_type in method_matches:
        result['methods'].append({
            'name': name,
            'parameters': params.strip(),
            'return_type': return_type.strip() if return_type else None,
        })

    # 特定の種類のファイルかどうかを判断
    if result['class_name']:
        if result['class_name'].endswith('ViewModel'):
            result['is_viewmodel'] = True
        elif result['class_name'].endswith('View'):
            result['is_view'] = True
        elif result['class_name'].endswith('Model'):
            result['is_model'] = True
        elif 'Repository' in result['class_name']:
            result['is_repository'] = True
        elif 'Service' in result['class_name']:
            result['is_service'] = True

    # 特定のフレームワークの使用を検出
    result['uses_combine'] = 'Combine' in result['imports'] or 'Publisher' in content or 'Subject' in content
    result['uses_swiftdata'] = 'SwiftData' in result['imports'] or '@Model' in content
    result['uses_firebase'] = 'Firebase' in result['imports'] or 'FirebaseAuth' in content

    return result

def parse_kotlin_template(content: str) -> Dict[str, Any]:
    """
    Kotlin テンプレートファイルの内容を解析します。

    Args:
        content: Kotlin ファイルの内容

    Returns:
        解析結果を含む辞書
    """
    result = {
        'imports': [],
        'package': None,
        'class_name': None,
        'superclass': None,
        'interfaces': [],
        'properties': [],
        'methods': [],
        'is_data_class': False,
        'is_sealed_class': False,
        'is_enum_class': False,
        'is_interface': False,
        'is_object': False,
        'is_viewmodel': False,
        'is_composable': False,
        'uses_flow': False,
        'uses_livedata': False,
        'uses_room': False,
        'uses_firebase': False,
    }

    # パッケージを抽出
    package_pattern = r'package\s+([^\n]+)'
    package_match = re.search(package_pattern, content)
    if package_match:
        result['package'] = package_match.group(1).strip()

    # インポートを抽出
    import_pattern = r'import\s+([^\n]+)'
    result['imports'] = re.findall(import_pattern, content)

    # クラス定義を抽出
    class_pattern = r'(class|interface|object|sealed class|data class|enum class)\s+(\w+)(?:\s*:\s*([^{]+))?'
    class_matches = re.findall(class_pattern, content)

    if class_matches:
        type_name, name, inheritance = class_matches[0]
        result['class_name'] = name.strip()

        if type_name == 'data class':
            result['is_data_class'] = True
        elif type_name == 'sealed class':
            result['is_sealed_class'] = True
        elif type_name == 'enum class':
            result['is_enum_class'] = True
        elif type_name == 'interface':
            result['is_interface'] = True
        elif type_name == 'object':
            result['is_object'] = True

        # 継承関係を解析
        if inheritance:
            inheritance_parts = [part.strip() for part in inheritance.split(',')]
            if inheritance_parts:
                result['superclass'] = inheritance_parts[0]
                result['interfaces'] = inheritance_parts[1:]

    # プロパティを抽出
    property_pattern = r'(?:val|var)\s+(\w+)\s*:\s*([^\n=]+)(?:\s*=\s*([^\n]+))?'
    property_matches = re.findall(property_pattern, content)

    for name, type_info, default_value in property_matches:
        result['properties'].append({
            'name': name,
            'type': type_info.strip(),
            'default_value': default_value.strip() if default_value else None,
        })

    # メソッドを抽出
    method_pattern = r'fun\s+(\w+)\s*\(([^)]*)\)\s*(?::\s*([^{]+))?'
    method_matches = re.findall(method_pattern, content)

    for name, params, return_type in method_matches:
        result['methods'].append({
            'name': name,
            'parameters': params.strip(),
            'return_type': return_type.strip() if return_type else None,
        })

    # 特定の種類のファイルかどうかを判断
    if result['class_name']:
        if result['class_name'].endswith('ViewModel'):
            result['is_viewmodel'] = True

    # Composable 関数を検出
    result['is_composable'] = '@Composable' in content

    # 特定のフレームワークの使用を検出
    result['uses_flow'] = 'Flow' in content or 'StateFlow' in content or 'SharedFlow' in content
    result['uses_livedata'] = 'LiveData' in content or 'MutableLiveData' in content
    result['uses_room'] = 'Room' in content or '@Entity' in content or '@Dao' in content
    result['uses_firebase'] = 'Firebase' in content or 'FirebaseAuth' in content

    return result

def swift_type_to_kotlin(swift_type: str) -> str:
    """
    Swift の型を Kotlin の型に変換します。

    Args:
        swift_type: Swift の型

    Returns:
        Kotlin の型
    """
    # 基本的な型の変換
    type_mapping = {
        'String': 'String',
        'Int': 'Int',
        'Double': 'Double',
        'Float': 'Float',
        'Bool': 'Boolean',
        'Character': 'Char',
        'Any': 'Any',
        'AnyObject': 'Any',
        'Void': 'Unit',
        'Never': 'Nothing',
        'Date': 'java.util.Date',
        'URL': 'java.net.URL',
        'Data': 'ByteArray',
        'UUID': 'java.util.UUID',
        'Dictionary<String, Any>': 'Map<String, Any>',
        'Dictionary<String, String>': 'Map<String, String>',
        'Array<String>': 'List<String>',
        'Array<Int>': 'List<Int>',
        '[String]': 'List<String>',
        '[Int]': 'List<Int>',
        '[String: Any]': 'Map<String, Any>',
        '[String: String]': 'Map<String, String>',
    }

    # オプショナル型の処理
    optional_pattern = r'(\w+)\?'
    optional_match = re.match(optional_pattern, swift_type)
    if optional_match:
        base_type = optional_match.group(1)
        kotlin_base_type = type_mapping.get(base_type, base_type)
        return f"{kotlin_base_type}?"

    # 配列型の処理
    array_pattern = r'Array<(.+)>'
    array_match = re.match(array_pattern, swift_type)
    if array_match:
        element_type = array_match.group(1)
        kotlin_element_type = swift_type_to_kotlin(element_type)
        return f"List<{kotlin_element_type}>"

    # 辞書型の処理
    dict_pattern = r'Dictionary<(.+),\s*(.+)>'
    dict_match = re.match(dict_pattern, swift_type)
    if dict_match:
        key_type = dict_match.group(1)
        value_type = dict_match.group(2)
        kotlin_key_type = swift_type_to_kotlin(key_type)
        kotlin_value_type = swift_type_to_kotlin(value_type)
        return f"Map<{kotlin_key_type}, {kotlin_value_type}>"

    # 短縮形の配列型の処理
    short_array_pattern = r'\[(.+)\]'
    short_array_match = re.match(short_array_pattern, swift_type)
    if short_array_match:
        element_type = short_array_match.group(1)
        kotlin_element_type = swift_type_to_kotlin(element_type)
        return f"List<{kotlin_element_type}>"

    # 短縮形の辞書型の処理
    short_dict_pattern = r'\[(.+):\s*(.+)\]'
    short_dict_match = re.match(short_dict_pattern, swift_type)
    if short_dict_match:
        key_type = short_dict_match.group(1)
        value_type = short_dict_match.group(2)
        kotlin_key_type = swift_type_to_kotlin(key_type)
        kotlin_value_type = swift_type_to_kotlin(value_type)
        return f"Map<{kotlin_key_type}, {kotlin_value_type}>"

    # 基本的な型の変換
    return type_mapping.get(swift_type, swift_type)

def swift_method_to_kotlin(method_name: str, parameters: str, return_type: Optional[str]) -> Tuple[str, str, Optional[str]]:
    """
    Swift のメソッドを Kotlin のメソッドに変換します。

    Args:
        method_name: メソッド名
        parameters: パラメータ
        return_type: 戻り値の型

    Returns:
        (Kotlin のメソッド名, Kotlin のパラメータ, Kotlin の戻り値の型) のタプル
    """
    # メソッド名の変換（キャメルケースを維持）
    kotlin_method_name = method_name

    # パラメータの変換
    kotlin_parameters = ""
    if parameters:
        param_parts = []
        for param in parameters.split(','):
            param = param.strip()
            if ':' in param:
                # Swift のパラメータ形式: name: Type または label name: Type
                parts = param.split(':')
                if len(parts) == 2:
                    param_name, param_type = parts
                    param_name = param_name.strip()
                    param_type = param_type.strip()
                    kotlin_param_type = swift_type_to_kotlin(param_type)
                    param_parts.append(f"{param_name}: {kotlin_param_type}")
                elif len(parts) == 3:
                    # ラベル付きパラメータの場合
                    _, param_name, param_type = parts
                    param_name = param_name.strip()
                    param_type = param_type.strip()
                    kotlin_param_type = swift_type_to_kotlin(param_type)
                    param_parts.append(f"{param_name}: {kotlin_param_type}")
            else:
                # 単純なパラメータの場合
                param_parts.append(param)

        kotlin_parameters = ", ".join(param_parts)

    # 戻り値の型の変換
    kotlin_return_type = None
    if return_type:
        kotlin_return_type = swift_type_to_kotlin(return_type)

    return kotlin_method_name, kotlin_parameters, kotlin_return_type