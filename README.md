# CCMB

Base de consulta de **Common Criteria CC:2022 Parte 2 Rev.1** (Security functional
components), con buscador y tema visual "space". Interfaz en espanol. El contenido
del documento se muestra **en espanol por defecto** (traducido), con un boton
"Ver en ingles" para consultar el texto original del PDF tal cual, palabra por
palabra, cuando haga falta precision normativa. La busqueda funciona en ambos
idiomas (tolerante a mayusculas y tildes).

## Estructura

```
build_db.py               Extrae el PDF y genera ccmb.db (SQLite + FTS5, en ingles)
export_for_translation.py Exporta el contenido de ccmb.db a JSON para traducir
apply_translations.py     Fusiona las traducciones (_es) de vuelta en ccmb.db
main.py                    Punto de entrada de la app / script para PyInstaller
app/
  db.py                     Acceso a datos (ccmb.db)
  render.py                 Construccion del HTML del panel de detalle (ES/EN)
  theme.py                   Paleta de colores y hoja de estilos QSS
  widgets.py                 Fondo "hero", barra de busqueda con glow
  main.py                    Ventana principal (arbol, buscador, navegacion)
assets/
  icon.ico / icon.png        Icono de la app
CC2022PART2R1.pdf          Fuente (solo para generar la base; no se empaqueta)
ccmb.db                    Base de datos generada (ingles + espanol embebidos)
requirements.txt
build.bat                  Genera dist\CCMB.exe y, si hay Inno Setup, el instalador
installer.iss               Script de Inno Setup (instalador con asistente)
```

## Desarrollo

```bash
python -m venv venv
venv\Scripts\activate        # o: source venv/bin/activate en Linux/Mac
pip install -r requirements.txt

# 1) Generar la base de datos desde el PDF (una sola vez, o cuando cambie el PDF)
python build_db.py CC2022PART2R1.pdf ccmb.db

# 2) Correr la app
python main.py
```

`build_db.py` imprime un reporte de verificacion: cantidad de clases/familias/
componentes cargados, chequeos puntuales de dependencias (FAU_ARP.1 -> FAU_SAA.1,
FAU_GEN.2 -> FAU_GEN.1 + FIA_UID.1) y advertencias sobre componentes incompletos.

### Traduccion al espanol

`ccmb.db` ya incluye las traducciones (columnas `*_es`). Si se regenera la base
desde cero con `build_db.py` (por ejemplo tras actualizar el PDF), hay que volver
a traducir el contenido nuevo:

```bash
python export_for_translation.py   # vuelca el contenido a translation_batches/*.json
# traducir cada batchN.json -> batchN_es.json (completando los campos "_es")
python apply_translations.py       # fusiona las traducciones de vuelta en ccmb.db
```

## Empaquetado (.exe + instalador, Windows)

Todo este paso se corre **en una PC con Windows** (PyInstaller e Inno Setup no
son multiplataforma; no se puede generar el `.exe` desde Linux/Mac).

1. Instala [Python 3.10+](https://www.python.org/downloads/) (con "Add to PATH").
2. (Opcional, para el instalador con asistente) Instala
   [Inno Setup 6](https://jrsoftware.org/isdl.php) (gratis).
3. Corre `build.bat` desde una consola (doble clic tambien funciona). El script:
   - crea un entorno virtual e instala dependencias,
   - genera `ccmb.db` desde el PDF si todavia no existe,
   - empaqueta todo con PyInstaller en `dist\CCMB.exe` (ejecutable portable,
     funciona solo con copiar ese archivo, sin instalar nada),
   - si detecta Inno Setup instalado, ademas genera
     `installer_output\CCMB_Setup.exe` (instalador con asistente: copia la app
     a Archivos de programa, crea accesos directos y desinstalador).

Para mandarle la app a alguien, lo mas simple es enviarle **`CCMB_Setup.exe`**
(instalador) o, si no tenes Inno Setup, directamente **`dist\CCMB.exe`** (no
necesita instalacion, ni el PDF, ni Python: todo queda embebido en el archivo).
