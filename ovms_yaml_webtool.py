import streamlit as st
import re
import yaml

def safe_search(pattern, text, group=1, flags=0, default=None, cast=str):
    match = re.search(pattern, text, flags)
    try:
        return cast(match.group(group))
    except:
        return default

def parse_extended_bms_diag(text: str) -> dict:
    text = text.replace('\u2028', '\n').replace('\u2029', '\n').replace('\xa0', ' ').replace('\u200b', '').replace('\ufeff', '')
    text = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', text)

    data = {}
    data['vin'] = safe_search(r'VIN\s*:\s*(\w+)', text)
    data['time'] = safe_search(r'Time\s*\[hh:mm\]:\s*([\d:]+)', text)
    data['odometer_km'] = safe_search(r'ODO\s*:\s*(\d+)', text, cast=int)
    data['status'] = safe_search(r'Battery Status\s*:\s*(\w+)', text)
    data['production_date'] = safe_search(r'Battery Production \[Y/M/D\]:\s*([\d/]+)', text, cast=lambda x: x.replace('/', '-'))
    data['fat_date'] = safe_search(r'Battery-FAT date\s*\[Y/M/D\]:\s*([\d/]+)', text, cast=lambda x: x.replace('/', '-'))
    data['revision'] = {
        'hardware': safe_search(r'Rev\.\[Y/WK/PL\]\s*HW:([\d/]+)', text),
        'software': safe_search(r'Rev\.\[Y/WK/PL\].*?SW:([\d/]+)', text)
    }
    data['soc'] = {
        'displayed': safe_search(r'SOC\s*:\s*([\d.]+)%', text, cast=float),
        'real': safe_search(r'realSOC:\s*([\d.]+)%', text, cast=float)
    }
    data['hv'] = {
        'voltage_v': safe_search(r'HV\s*:\s*([\d.]+)\s*V', text, cast=float),
        'current_a': safe_search(r'HV\s*:\s*[\d.]+\s*V,\s*([-\.\d]+)\s*A', text, cast=float),
        'power_kw': safe_search(r'HV\s*:\s*[\d.]+\s*V,\s*[-\.\d]+\s*A,\s*([\d.]+)\s*kW', text, cast=float)
    }
    data['lv'] = {
        'voltage_v': safe_search(r'LV\s*:\s*([\d.]+)\s*V', text, cast=float),
        'soc': safe_search(r'LV\s*:\s*[\d.]+\s*V,\s*([\d.]+)\s*%', text, cast=float)
    }
    data['cell_voltage'] = {
        'mean_mv': safe_search(r'CV mean\s*:\s*(\d+)\s*mV', text, cast=int),
        'delta_mv': safe_search(r'dV\s*=\s*([\d.]+)\s*mV', text, cast=float),
        'min_mv': safe_search(r'CV min\s*:\s*(\d+)\s*mV', text, cast=int),
        'max_mv': safe_search(r'CV max\s*:\s*(\d+)\s*mV', text, cast=int),
        'ocv_timer_s': safe_search(r'OCVtimer:\s*(\d+)\s*s', text, cast=int)
    }
    cell_lines = re.findall(r'^\s*(\d+);\s*(\d+);\s*(\d+)', text, re.MULTILINE)
    data['cell_data'] = [{'id': int(c[0]), 'mv': int(c[1]), 'as10': int(c[2])} for c in cell_lines]
    return {'battery_diagnostics': data}

def convert_to_yaml(text: str) -> str:
    data = parse_extended_bms_diag(text)
    return yaml.dump(data, sort_keys=False, allow_unicode=True)

# Streamlit UI
st.title("OVMS BMS Text zu YAML Konverter")
uploaded_file = st.file_uploader("Lade deine BMS-Diagnose-Datei hoch (.txt)", type=["txt"])
if uploaded_file:
    content = uploaded_file.read().decode("utf-8")
    yaml_output = convert_to_yaml(content)
    st.download_button("YAML herunterladen", data=yaml_output, file_name="bms_output.yaml")
    st.text_area("Vorschau YAML", yaml_output, height=400) 
