from pathlib import Path


def run_automated_tests(test_dir_path: str) -> bool:
    full_path = Path(test_dir_path) / "in.txt"
    if not full_path.is_file():
        print(f"A fájl {full_path} nem létezik")
        return False
    
    lines = []
    with open(full_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    for line in lines:
        if not line.strip():
            continue
        
        parts   = [part.strip() for part in line.strip().split(";")]
        command = parts[0].lower()

        match command:
            case "uj kartya"             : pass
            case "uj vezer"              : pass
            case "uj kazamata"           : pass
            case "uj jatekos"            : pass
            case "felvetel gyujtemenybe" : pass
            case "uj pakli"              : pass
            case "harc"                  : pass
            case "export vilag"          : pass
            case "export jatekos"        : pass
            case _                       : print(f"Ismeretlen parancs: {command}")
    

    return True