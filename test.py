text = """
{total:2, docs:[{"documentId":{"compound":false,"dataProviderId":"ce_bp8os_repository","properties":{"$os":"ADAMSPublicOS","ce_object_id":"{24C3D8B2-ED89-47F9-B4B4-B78502CA3260}","$is_compound":false,"$id":"{309ED6F2-96E5-CC6D-8DDD-8D1CC8400000}"}},"mimeType":"application/pdf","size":42017385,"title":"JA Volume 1","properties":{"AuthorName":["Averbach A P","Clark B P","Curran D","Goldstein M","Heminger J D","Kanner A","Kim T","Leidich A","Lodge T J","Perales M R","Silberg J E","Taylor W L","Tennis A"],"$size":"42,017,385","$mime_type":"application/pdf","LicenseNumber":[],"$title":"JA Volume 1","AccessionNumber":"ML24017A183","PublishDatePARS":"01/18/2024 08:33 AM EST","DocumentDate":"01/16/2024","$is_compound":"false "}},{"documentId":{"compound":false,"dataProviderId":"ce_bp8os_repository","properties":{"$os":"ADAMSPublicOS","ce_object_id":"{27A693D1-C6B7-4BD5-B0EE-68B6776DE56C}","$is_compound":false,"$id":"{6AE503F3-755D-CA84-87B2-8D1CC8600000}"}},"mimeType":"application/pdf","size":32072831,"title":"Deferred Joint Appendix - Volume II of II","properties":{"AuthorName":["Clark B P","Curran D","Goldstein M","Heminger J D","Kanner A","Kim T","Leidich A","Lodge T J","Perales M R","Silberg J E","Taylor W L","Tennis A"],"$size":"32,072,831","$mime_type":"application/pdf","LicenseNumber":[],"$title":"Deferred Joint Appendix - Volume II of II","AccessionNumber":"ML24017A184","PublishDatePARS":"01/18/2024 08:33 AM EST","DocumentDate":"01/16/2024","$is_compound":"false "}}]}

"""
import json
import re
def fix_json(json_str):
    # 正则表达式匹配未加引号的键名
    pattern = re.compile(r'(\b[a-zA-Z_][a-zA-Z0-9_]*\b):')
    
    # 使用正则表达式替换未加引号的键名为加引号的键名
    fixed_json_str = pattern.sub(r'"\1":', json_str)
    
    return fixed_json_str
# json_data = json.loads()
print(fix_json(text))