# Laboratorio de agentes de IA para DevOps

Un agente local investiga el fallo de una calculadora de costos, consulta evidencia mediante herramientas y propone una corrección. Una persona revisa la propuesta, autoriza su aplicación y abre un pull request. GitHub Actions vuelve a ejecutar las pruebas. No hay despliegue ni fusión automática.

Las tarifas son ficticias. No se consulta AWS, no se necesitan credenciales de nube y no se usa una API de IA de pago. La inferencia consume recursos de tu computador. Para los trabajos de CI sin cargo, esta guía usa un repositorio público y un runner estándar Ubuntu, sin artefactos ni cachés. Si prefieres un repositorio privado, revisa primero las cuotas y los límites de gasto de tu cuenta.

## 1. Preparar Windows

Instala desde sus sitios oficiales:

- Python 3.12: https://www.python.org/downloads/windows/ (incluye el lanzador `py`).
- Git: https://git-scm.com/downloads/win
- GitHub CLI: https://cli.github.com/
- Ollama: https://ollama.com/download/windows
- Opcional, Visual Studio Code: https://code.visualstudio.com/

Abre una nueva ventana de PowerShell después de instalar. Comprueba:

```powershell
py --version
git --version
gh --version
ollama --version
```

La aplicación solo usa la biblioteca estándar de Python; no hay dependencias que instalar con pip. No necesitas Docker, WSL ni Windows Pro.

Consulta memoria y espacio antes de descargar el modelo:

```powershell
Get-CimInstance Win32_ComputerSystem | Select-Object @{Name='RAM_GB';Expression={[math]::Round($_.TotalPhysicalMemory / 1GB)}}
Get-PSDrive C | Select-Object Name,@{Name='Libre_GB';Expression={[math]::Round($_.Free / 1GB)}}
```

Ollama indica al menos 4 GB de disco para su instalación, más el modelo. Como margen práctico para este laboratorio, intenta disponer de 15 GB libres; no es una especificación oficial del modelo. Con 16 GB de RAM comenzaría por qwen3:4b. Con 8 GB, probaremos qwen3:1.7b y cerraremos otras aplicaciones; su fiabilidad al usar herramientas puede ser menor. Esto es una orientación, no una garantía de velocidad o compatibilidad de GPU.

```powershell
ollama pull qwen3:4b
ollama list
```

Ollama debe estar abierto. La descarga necesita internet; la inferencia posterior se hace localmente. Mantén el servicio en su dirección local predeterminada. El agente se conecta a `127.0.0.1:11434`.

## 2. Entender el caso

Extrae el ZIP y abre PowerShell en la carpeta que contiene `costs.py`. En el Explorador puedes escribir `powershell` en la barra de dirección y pulsar Enter.

La función recibe tarifa por hora, horas y cantidad de instancias. Con una tarifa ficticia de 0,10, diez horas y tres instancias, el resultado esperado es 3,00. La versión inicial suma las instancias en lugar de multiplicarlas: devuelve 4,00. Este error intencional hará fallar seis pruebas; la validación de valores negativos sí pasa.

Archivos principales:

| Archivo | Función |
|---|---|
| costs.py | Aplicación con el error intencional |
| tests/test_costs.py | Siete pruebas de comportamiento |
| .github/workflows/ci.yml | Pipeline que ejecuta las pruebas |
| agent.py | Bucle del agente, herramientas y conexión local con Ollama |
| lab.py | Captura de evidencia y aplicación revisada de la propuesta |
| output/ | Registros y propuestas generados; excluidos de Git |

## 3. Primer ensayo sin GitHub

```powershell
py lab.py record
py agent.py
Get-Content output\proposal.md -Encoding UTF8
```

El primer comando ejecuta las pruebas y guarda el fallo. El segundo consulta el modelo. Espera ver llamadas a `read_failure`, `read_source`, `read_tests` y `propose_formula`; su orden puede variar. El modelo decide qué herramienta usar. El controlador valida los argumentos y limita el proceso a diez consultas. La propuesta no contiene una solución precargada: debe generarla el modelo.

Para el modelo pequeño, sustituye el segundo comando por:

```powershell
py agent.py --model qwen3:1.7b
```

Debes haber descargado previamente ese modelo con `ollama pull qwen3:1.7b`.

Revisa la explicación y la fórmula. Para conservar el fallo inicial y subirlo a GitHub, NO apliques todavía la propuesta. Continúa con el paso 4. Si solo quieres probar localmente, ejecuta `py lab.py apply`, revisa el diff y escribe `APLICAR`; después usa una nueva extracción del ZIP para iniciar el recorrido de GitHub desde el fallo original.

## 4. Crear el repositorio del laboratorio

Inicia sesión mediante el navegador; no copies tokens al código ni al chat:

```powershell
gh auth login
gh auth setup-git
git init -b main
```

Si Git no tiene tu identidad, configúrala para este repositorio. Sustituye el correo por tu dirección noreply de GitHub, disponible en Settings > Emails, o por la dirección que decidas publicar:

```powershell
git config user.name "Liz Bareno"
git config user.email "TU_CORREO_NOREPLY_DE_GITHUB"
git add .
git commit -m "Laboratorio inicial con fallo reproducible"
gh repo create laboratorio-agente-devops --public --source=. --remote=origin --push
```

El último comando publica estos archivos. Usa un nombre distinto si ya tienes ese repositorio. No incluyas archivos de tu trabajo ni datos personales. Esta guía no crea el repositorio por ti.

Espera a que aparezca la ejecución:

```powershell
gh run list --limit 5
```

Identifica el ID numérico del trabajo fallido y reemplaza `123456789` en los siguientes comandos:

```powershell
gh run view 123456789
py lab.py record --run 123456789
```

El script exige que el trabajo haya terminado con fallo y que su commit coincida con el código local. La captura local del paso 3 queda sustituida por los registros reales de GitHub Actions.

## 5. Analizar y aplicar la propuesta

```powershell
py agent.py
Get-Content output\proposal.md -Encoding UTF8
git switch -c fix/propuesta-agente
py lab.py apply
```

El último comando muestra el cambio y solicita `APLICAR`. Solo puede modificar una expresión de retorno en costs.py. Ejecuta las siete pruebas; si fallan, restaura el archivo original. Las pruebas y el pipeline no se pueden modificar mediante las herramientas del agente.

Comprueba los resultados:

```powershell
git diff -- costs.py
Get-Content output\validation.txt -Encoding UTF8
```

Debes obtener siete pruebas correctas. Si el agente no logra una propuesta válida, no se considera éxito: conserva la traza y revisa el comportamiento antes de la conferencia.

## 6. Abrir el pull request

La publicación requiere una acción explícita tuya. El modelo no tiene una herramienta de GitHub ni recibe las credenciales de gh.

```powershell
git add costs.py
git commit -m "Corregir calculo de costos con propuesta revisada"
git push -u origin fix/propuesta-agente
gh pr create --base main --head fix/propuesta-agente --title "Corregir calculo de costos" --body "Propuesta generada por un modelo local y revisada por una persona. Se corrige la formula de costos. Las siete pruebas locales pasan; pendiente comprobar CI."
gh pr checks --watch
gh pr view --web
```

La creación del PR dispara CI. Revisa Files changed y Checks en GitHub. Para la demo puedes dejarlo abierto; no hay necesidad de fusionarlo. En tu propio repositorio puedes revisar y fusionar, pero no aprobar formalmente tu propio PR como un revisor independiente. Para mostrar esa aprobación formal necesitarías otra persona.

## 7. Guion de demostración de 10 a 15 minutos

1. Presenta el cálculo esperado y muestra CI en rojo.
2. Explica que el pipeline ejecuta reglas; el agente consulta evidencia y propone.
3. Captura el registro de GitHub y lanza el agente local.
4. Muestra qué herramientas invocó y la propuesta guardada.
5. Revisa el diff, autoriza la aplicación y muestra las pruebas correctas.
6. Abre el PR y muestra CI en verde.
7. Cierra con el límite del caso: una fórmula controlada y pruebas concretas; pasar estas pruebas no demuestra que un agente pueda reparar cualquier sistema.

Antes del evento, ensaya con el mismo equipo, registra la duración y graba un recorrido exitoso. Una grabación de respaldo debe identificarse como grabación. Si la conexión falla, puedes repetir el análisis local con evidencia ya descargada; publicar el PR y usar Actions sí necesitan internet.

Para repetir sin perder trabajo, conserva el PR anterior abierto y usa una nueva carpeta/clon desde main, que sigue teniendo el fallo. Usa otro nombre para la rama de corrección. No ejecutes comandos de borrado o reset para reiniciar la demo.

## 8. Límites y solución de problemas

- `py`, `gh`, `git` u `ollama` no se reconocen: cierra y abre PowerShell; verifica la instalación correspondiente.
- Conexión rechazada al puerto 11434: abre Ollama. Comprueba `ollama list`.
- Modelo no encontrado: ejecuta `ollama pull` con el mismo nombre que usas en el agente.
- Equipo lento o consulta agotada: reduce el modelo, cierra aplicaciones y vuelve a ensayar. No se promete una duración fija en CPU.
- Límite de diez consultas: consulta `output/trace.json`. El modelo puede fallar al usar herramientas o proponer una fórmula; no hay corrección automática de respaldo disfrazada de IA.
- Propuesta desactualizada: vuelve a capturar evidencia y ejecutar el agente sobre el código actual.
- Este controlador solo admite las tres variables y operadores aritméticos limitados. No es un sandbox general para ejecutar código generado ni debe ampliarse para aceptar comandos arbitrarios.
- La ejecución local de pruebas presupone que usas estos archivos de confianza. No ejecutes código desconocido descargado de otros repositorios.
- La integración con Windows, Ollama y tu cuenta de GitHub debe verificarse en tu equipo. Las pruebas incluidas verifican la aplicación; no garantizan la calidad del modelo.

## Fuentes oficiales consultadas

- Windows y Ollama: https://docs.ollama.com/windows
- Uso de herramientas: https://docs.ollama.com/capabilities/tool-calling
- Modelo: https://ollama.com/library/qwen3:4b
- Condiciones de Actions: https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Checkout: https://github.com/actions/checkout
- Python en Actions: https://github.com/actions/setup-python

Consulta de referencias: 10 de octubre de 2026.
