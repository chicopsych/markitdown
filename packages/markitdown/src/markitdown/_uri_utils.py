import base64
import os
from typing import Tuple, Dict
from urllib.request import url2pathname
from urllib.parse import urlparse, unquote_to_bytes


def file_uri_to_path(file_uri: str) -> Tuple[str | None, str]:
    """
    Converte uma URI de arquivo (file://) para um caminho de arquivo local.

    Args:
        file_uri: A URI do arquivo (ex: file:///C:/path/to/file.txt).

    Returns:
        Uma tupla contendo (netloc, path).
        - netloc: O local da rede (geralmente None para arquivos locais).
        - path: O caminho absoluto do arquivo no sistema operacional.
    """
    parsed = urlparse(file_uri)
    if parsed.scheme != "file":
        raise ValueError(f"Não é uma URL de arquivo: {file_uri}")

    netloc = parsed.netloc if parsed.netloc else None
    # url2pathname converte a codificação da URL (%20) para caminhos do sistema operacional
    # os.path.abspath garante que temos um caminho absoluto normalizado
    path = os.path.abspath(url2pathname(parsed.path))
    return netloc, path


def parse_data_uri(uri: str) -> Tuple[str | None, Dict[str, str], bytes]:
    """
    Analisa uma URI de dados (data:...) e extrai seu conteúdo e metadados.

    Formato esperado: data:[<mediatype>][;base64],<data>

    Returns:
        Uma tupla contendo:
        - mime_type: O tipo MIME do dado (ex: 'image/png'), ou None.
        - attributes: Um dicionário de atributos adicionais (ex: charset).
        - content: O conteúdo decodificado em bytes.
    """
    if not uri.startswith("data:"):
        raise ValueError("Não é uma URI de dados")

    # Separa o cabeçalho dos dados reais na primeira vírgula
    header, _, data = uri.partition(",")
    if not _:
        raise ValueError("URI de dados malformada, separador ',' ausente")

    # Remove o prefixo 'data:' para analisar os metadados
    meta = header[5:]
    parts = meta.split(";")

    is_base64 = False
    # Verifica se a última parte indica codificação base64
    if parts and parts[-1] == "base64":
        parts.pop()
        is_base64 = True

    mime_type = None
    # Se houver partes restantes, a primeira é geralmente o mime_type
    if parts and len(parts[0]) > 0:
        mime_type = parts.pop(0)

    attributes: Dict[str, str] = {}
    for part in parts:
        # Processa pares chave=valor nos metadados (ex: charset=utf-8)
        if "=" in part:
            key, value = part.split("=", 1)
            attributes[key] = value
        elif len(part) > 0:
            attributes[part] = ""

    # Decodifica o conteúdo baseado no sinalizador base64 ou decodificação de URL padrão
    content = base64.b64decode(data) if is_base64 else unquote_to_bytes(data)

    return mime_type, attributes, content
