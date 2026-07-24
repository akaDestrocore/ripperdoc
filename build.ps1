$ErrorActionPreference = "Stop"

pyinstaller `
    --onefile `
    --windowed `
    --name RIPPERDOC `
    --icon favicon.ico `
    --add-data "tools_gui/i18n/en.json;tools_gui/i18n" `
    --add-data "tools_gui/i18n/tr.json;tools_gui/i18n" `
    --add-data "favicon.ico;." `
    app.py