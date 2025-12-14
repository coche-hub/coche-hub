# Documento del Proyecto

**Coche-hub:**  


- **Grupo:** 2 
- **Curso escolar:** 2025/2026
- **Asignatura:** Evolución y gestión de la configuración

---

## Miembros del grupo

*(en orden alfabético según apellido)*

- Herrera Romero, Jose Ángel
- Milá de la roca dos Santos, Javier Ignacio
- Palmas Santos, Carlos
- Ortega Almirón, Raquel
- Toledo González, Manuel
- Sánchez Ruiz, Ángel

---

## Indicaciones generales

- Diferencie claramente secciones y subsecciones
- Utilice encabezados Markdown (`#`, `##`, `###`)
- Incluya enlaces a evidencias siempre que sea posible (gráficas, issues, commits, dashboards, etc.)

---

## Indicadores del proyecto

> Deben incluirse enlaces a evidencias que permitan analizar los indicadores de forma sencilla (gráficas y/o enlaces).

| Miembro del equipo | Horas | Commits | LoC | Test | Issues | Work Item | Dificultad |
|-------------------|-------|---------|-----|------|--------|-----------|------------|
| Herrera Romero, Jose Ángel | 13,5   | 11     | 1498  | 29   | 3     | Trabajo en la recomendación de coches y en fakenodo| H |
| Milá de la roca dos Santos, Javier Ignacio | 34    | 33      | 3323  | 67   | 9    | Trabajo en email validation y el 2fa | H  y L |
|Palmas Santos, Carlos| 25    | 26     | 3295  | 27   | 8     | Trabajo en la creación de comunidades| L |
|Ortega Almirón, Raquel| 15    | 9      | 1870  | 25   | 4     | Trabajo en advanced datset search| M |
|Toledo González, Manuel| 17    | 14  | 2908 | 23   | 7     | Trabajo en exploration by communities breve |  M  |
|Sánchez Ruiz, Ángel| 22    | 14      | 2520  |  30  | 14     | Trabajo en new dataset | H |
| **TOTAL**         | 126,5  | 101    | 14849 | 175  | 44    | Se completaron todos los work items| H(3) / M(2) / L(2) |

### Definición de indicadores

- **Horas:** Número total de horas empleadas en el proyecto
- **Commits:** Solo commits realizados por los miembros del equipo
- **LoC (Lines of Code):** Líneas producidas por el equipo (no código previo ni de terceros)
- **Test:** Tests nuevos desarrollados por el equipo
- **Issues:** Issues gestionadas dentro del proyecto por el equipo
- **Work Item:** Principal elemento de trabajo del que se ha encargado cada miembro
- **Dificultad:**  
  - H: Alta  
  - M: Media  
  - L: Baja  
  En el total se indicará cuántos elementos hay de cada tipo

### Evidencias
-**Test:**https://github.com/coche-hub/coche-hub/commits/main/app/modules/auth/tests/test_unit.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/auth/tests/test_email_2fa.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/auth/tests/test_email_validation.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/dataset/tests/test_unit.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/dataset/tests/test_recommendation.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/explore/tests/test_repository.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/explore/tests/test_routes.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/explore/tests/test_service.py
https://github.com/coche-hub/coche-hub/commits/main/app/modules/fakenodo/tests
https://github.com/coche-hub/coche-hub/commits/main/app/modules/community/tests?author=JoseAngelHerrera
https://github.com/coche-hub/coche-hub/commit/f01d9db974a98b3215966a365b8d7a3be4e9c382
https://github.com/coche-hub/coche-hub/commit/34209f4cec4ba9f93e31e283c98c8a9824e1854f
https://github.com/coche-hub/coche-hub/commit/10b5e8b267edad68adc01a2c592911aef2dd240e
https://github.com/coche-hub/coche-hub/commit/2b0740183941d7d9adced5aa1d2869a7997af4aa

-**Issues:** https://github.com/orgs/coche-hub/projects/3
-**commits y loc:** https://github.com/coche-hub/coche-hub/graphs/contributors



-**
---


## Resumen ejecutivo

El presente proyecto, desarrollado por el Grupo 2 en el marco de la asignatura "Evolución y gestión de la configuración" del curso académico 2025/2026, tiene como objetivo principal la evolución y el mantenimiento profesional de la plataforma **uvl-hub** en **coche-hub**. Este trabajo no solo se centra en la implementación técnica de nuevas funcionalidades, sino también en el establecimiento de un entorno de desarrollo colaborativo riguroso, centrandose en la integración y despliegue continuos

### Objetivos

Los objetivos fundamentales que han guiado este proyecto son:

1.  **Evolución Funcional:** Ampliar las capacidades de Coche-hub mediante la implementación de características avanzadas y necesarias para una plataforma moderna de gestión de datos y comunidades. Esto incluye desde la seguridad (autenticación por correo electrónico y autenticación de dos factores) hasta la usabilidad (exploración y búsqueda avanzada).
2.  **Calidad y Fiabilidad:** Asegurar la robustez del código mediante una amplia cobertura de pruebas unitarias y de integración y de interfaz garantizando que cada nueva característica no solo funcione, sino que sea mantenible.
3.  **Gestión de la Configuración:** Aplicar prácticas estrictas de control de versiones, ramas y revisiones de código para gestionar el trabajo concurrente de seis desarrolladores.


### Trabajo Realizado

El equipo ha trabajado de manera coordinada siguiendo una metodología ágil adaptada, con reuniones de seguimiento (7 en total, presenciales y virtuales) y una estructura clara de responsabilidades. Se establecieron políticas firmes desde el inicio (Actas 2025-01 a 2025-03) cubriendo aspectos como asistencia, uso responsable de IA y estándares de commits.

El desarrollo técnico se ha dividido en "Work Items" específicos asignados a cada miembro, cubriendo áreas críticas del sistema:
*   **Seguridad:** Implementación de validación por email y autenticación de dos factores (2FA), elevando el estándar de seguridad de la plataforma.
*   **Comunidades:** Creación y gestión de comunidades, permitiendo a los usuarios agruparse y colaborar, junto con funcionalidades de exploración específicas por comunidad.
*   **Datos (Datasets):** Mejoras significativas en la búsqueda avanzada de datasets, cambiando el funcionamiento de uvls a funcionar con coches y sistemas de recomendación para conectar usuarios con información relevante.
*   **Infraestructura:** Integración de "fakenodo" para simulación y pruebas.

Cada miembro ha asumido la responsabilidad completa de su módulo, desde el análisis y diseño hasta la implementación y pruebas, asegurando la integración continua con la rama trunk.

### Resultados Obtenidos

El resultado es una versión evolucionada de uvl-hub en coche-hub que es funcionalmente más rica . Se han cumplido el 100% de los Work Items planificados, integrando con éxito todas las ramas de tareas en el producto final.

Los logros más destacados incluyen:
*   Un sistema de autenticación seguro y verificado.
*   Una experiencia de usuario mejorada mediante búsquedas avanzadas y recomendaciones personalizadas.
*   Una arquitectura modular que ha permitido el trabajo paralelo sin conflictos bloqueantes.
*   Una base de código limpia y documentada, respaldada por una batería de pruebas exhaustiva.

### Datos Fundamentales del Proyecto

El esfuerzo y la magnitud del trabajo realizado se reflejan en las siguientes métricas clave consolidadas al final del periodo de desarrollo:

*   **Esfuerzo Total:** 126,5 horas dedicadas por el equipo.
*   **Volumen de Código:** 14.849 Líneas de Código (LoC) producidas, reflejando una alta productividad.
*   **Actividad de Desarrollo:** 101 Commits realizados, demostrando un flujo de trabajo constante e incremental.
*   **Calidad:** 175 Tests nuevos implementados, asegurando la estabilidad de las nuevas funciones.
*   **Gestión:** 44 Issues gestionadas y cerradas, evidenciando un seguimiento detallado de tareas y errores.
*   **Complejidad:** El equipo ha abordado con éxito una mezcla equilibrada de tareas de alta (3), media (2) y baja (2) complejidad, demostrando capacidad para resolver problemas técnicos difíciles.

En conclusión, el proyecto no solo cumple con los requisitos académicos de la asignatura, sino que entrega un producto software viable y mejorado, resultado de un proceso de ingeniería disciplinado y colaborativo.

---

## Descripción del sistema

### Visión Funcional

**Coche-hub** es una plataforma web colaborativa diseñada para facilitar el intercambio, la exploración y la gestión de conjuntos de datos (datasets) relacionados con el ámbito automovilístico. Funciona como un repositorio centralizado donde investigadores y entusiastas pueden:

*   **Publicar y Compartir:** Subir datasets a un almacenamiento seguro y persistente (integración simulada con Zenodo).
*   **Explorar y Descubrir:** Utilizar herramientas de búsqueda avanzada para localizar datos específicos basándose en metadatos, características o comunidades.
*   **Colaborar en Comunidades:** Unirse a grupos temáticos ("Comunidades") para compartir recursos y conocimientos de forma focalizada.


El sistema prioriza la usabilidad y la seguridad, ofreciendo flujos de trabajo claros para la subida de datos y garantizando la integridad de los usuarios mediante autenticación robusta.

### Visión Arquitectónica

El sistema sigue una arquitectura de **Monolito Modular** basada en el miniframework **Flask**. Esta decisión de diseño permite mantener la simplicidad de despliegue de un monolito, pero con la organización y separación de responsabilidades típica de los microservicios, facilitando el trabajo paralelo de múltiples desarrolladores.

El núcleo de la arquitectura se divide en:

1.  **Core (Nucleo):** Gestiona las funcionalidades transversales del sistema.
    *   *Managers:* Controladores para Configuración, Logging, Errores y Carga de Módulos.
    *   *Base de Datos:* Configuración centralizada de SQLAlchemy.
2.  **Modules (Módulos):** Componentes funcionales independientes que encapsulan su propia lógica, modelos y rutas (Blueprints).
    *   `auth`: Gestión de usuarios, sesiones y seguridad.
    *   `dataset`: Lógica de negocio principal para los datasets (CRUD, sincronización).
    *   `community`: Gestión de comunidades y pertenencia.
    *   `explore`: Funcionalidades de búsqueda y filtrado.
    *   `fakenodo`: Módulo de simulación para entornos de desarrollo.
    *   `zenodo`: Cliente de integración con la API de Zenodo.
    *   `profile`: Gestión de usuarios y sesiones.
    *   `etc`

La comunicación entre módulos se realiza mediante llamadas directas a servicios internos, manteniendo el acoplamiento bajo gracias a interfaces de servicio bien definidas.

### Visión Técnica

El stack tecnológico seleccionado prioriza la robustez y el ecosistema de código abierto (FLOSS):

*   **Backend:** Python 3 con Flask como framework web.
*   **Base de Datos:** MySQL para persistencia de datos relacionales (usuarios, metadatos, relaciones).
*   **ORM:** SQLAlchemy para la abstracción de base de datos y gestión de migraciones (Alembic).
*   **Búsqueda:** Elasticsearch para indexación y búsquedas complejas de alto rendimiento.
*   **Colas y Caché:** Redis y RQ (Redis Queue) para tareas en segundo plano y cacheo de sesiones.
*   **Infraestructura:** Docker y Docker Compose para la orquestación de contenedores, asegurando consistencia entre entornos de desarrollo y producción.


### Cambios Desarrollados

Durante este proyecto, el sistema base ha sido ampliado con las siguientes funcionalidades críticas:

1.  **Seguridad Avanzada (Módulo Auth):**
    *   Implementación de autenticación de dos factores (2FA) mediante TOTP.
    *   Sistema de validación y verificación de cuentas por correo electrónico.

2.  **Gestión de Comunidades (Módulo Community):**
    *   Nueva arquitectura de base de datos para soportar comunidades.
    *   Interfaces para crear, editar y unirse a comunidades.
    *   Vinculación de datasets a comunidades específicas.

3.  **Búsqueda y Exploración (Módulo Explore/Dataset):**
    *   Motor de búsqueda avanzado con filtros dinámicos (autor, etiquetas, fecha).
    *   Sistema de recomendación de datasets basado en similitud.

4.  **Simulación y Testing (Módulo Fakenodo):**
    *   Desarrollo de `fakenodo`, un servidor mock que simula la API de Zenodo. Esto permite realizar pruebas de integración completas sin depender de la disponibilidad o límites de la API externa real, acelerando el ciclo de desarrollo y CI.

5.  **Calidad de Código:**
    *   Adición masiva de tests unitarios y de integración para los nuevos módulos.
    *   Refactorización de rutas para adherirse a principios RESTful.

---

## Visión global del proceso de desarrollo

### Metodología y principios de trabajo

El equipo ha adoptado una metodología ágil basada en principios de SCRUM adaptados a las necesidades específicas del proyecto CocheHub. Esta adaptación nos permite mantener la flexibilidad y la capacidad de respuesta rápida ante cambios, sin la sobrecarga administrativa que conllevaría una implementación estricta de SCRUM.

El pilar fundamental de nuestro proceso es el **Trunk-Based Development**, una estrategia de ramificación que promueve la integración continua y reduce significativamente los conflictos de merge. En este modelo, mantenemos una rama principal (`trunk`) donde se integra el trabajo de forma regular, y una rama `main` que representa el código en producción. Las ramas de características (`feature/`) y correcciones urgentes (`hotfix/`) son efímeras: se crean para un propósito específico y se eliminan inmediatamente después de su integración, evitando así la proliferación de ramas obsoletas que dificultan el mantenimiento del repositorio.

Esta filosofía de trabajo se complementa con los principios de **Integración Continua (CI)**, donde cada cambio que se integra en `trunk` debe pasar por un conjunto de verificaciones automáticas antes de ser aceptado. Esto garantiza que el código en la rama principal siempre esté en un estado deployable, lo que nos permite realizar despliegues frecuentes y reducir el riesgo asociado a cada liberación.

### Ecosistema de herramientas

El desarrollo de CocheHub se apoya en un conjunto integrado de herramientas que cubren todo el ciclo de vida del software, desde la planificación hasta el despliegue en producción.

**GitHub** actúa como el núcleo central de nuestro ecosistema, proporcionando no solo el control de versiones con Git, sino también la gestión de proyecto a través de **GitHub Projects**. Esta herramienta nos permite visualizar el estado del trabajo en tableros Kanban, donde las issues transitan por diferentes columnas (To Do, In Progress, Done) reflejando su estado actual. Cada issue sigue una plantilla estructurada que incluye contexto, solución propuesta, asignados y revisores, lo que facilita la comprensión del trabajo a realizar y asegura que todos los miembros del equipo tengan la información necesaria.

El entorno de desarrollo local se centra en **Visual Studio Code**, un editor extensible que hemos configurado con extensiones específicas para Python, Flask, y herramientas de calidad de código. Destaca el uso de **Live Share** para sesiones de pair programming, permitiendo la colaboración en tiempo real cuando se requiere trabajo conjunto en tareas complejas. El proyecto incluye además la herramienta **rosemary**, una CLI personalizada que facilita tareas comunes como la ejecución de tests (`rosemary test`), pruebas de interfaz con Selenium (`rosemary selenium`), y otras operaciones de desarrollo.

La gestión de dependencias y el aislamiento del entorno se realiza mediante **entornos virtuales de Python (venv)**, garantizando que cada desarrollador trabaje con las mismas versiones de librerías especificadas en `requirements.txt`. La base de datos MySQL se gestiona con **Alembic** para migraciones de esquema, permitiendo evolucionar la estructura de datos de forma controlada y reversible.

**GitHub Actions** implementa nuestro pipeline de CI/CD, ejecutando automáticamente verificaciones en cada commit que incluyen: validación del formato de mensajes de commit con **commit spell checker**, análisis estático de código con **Pylint** para asegurar el cumplimiento de estándares de calidad, y ejecución de la suite completa de tests con **Pytest** (incluyendo tests unitarios y de integración). Solo cuando todas estas verificaciones son exitosas, el código puede continuar su camino hacia producción.

La infraestructura de despliegue se basa en **Render**, donde mantenemos dos entornos separados: desarrollo y producción. Ambos utilizan **Docker** para el uso de contenedores, asegurando que la aplicación se ejecute en un entorno idéntico independientemente de dónde se despliegue. Los archivos `docker-compose` definen la arquitectura de servicios (aplicación Flask, base de datos MySQL, nginx como reverse proxy), facilitando tanto el desarrollo local como el despliegue en la nube.

### Flujo de trabajo estándar

El ciclo de vida de un cambio en CocheHub sigue un proceso bien definido que comienza en GitHub Projects y termina con código ejecutándose en producción. Cuando se identifica una necesidad (ya sea una nueva funcionalidad, una mejora o un bug), se crea una **issue en GitHub** utilizando las plantillas establecidas en el Acuerdo 2025-02-03. Esta issue debe incluir un título descriptivo, el contexto que explica el problema o necesidad, una propuesta de solución inicial, y la asignación de responsables (tanto para la implementación como para la revisión).

Una vez creada, la issue se etiqueta apropiadamente (bug, enhancement, documentation, etc.) y se mueve a la columna "In Progress" del tablero de GitHub Projects cuando un desarrollador comienza a trabajar en ella. El desarrollador entonces sincroniza su repositorio local (`git pull origin trunk`) para asegurarse de partir de la última versión del código.

El siguiente paso es la creación de una rama local siguiendo la convención de nombres establecida en el Acuerdo 2025-02-02. Para nuevas funcionalidades o mejoras se utiliza el prefijo `feature/` seguido de un nombre descriptivo (por ejemplo, `feature/add-country-filter`), mientras que para correcciones urgentes en producción se usa `hotfix/` (por ejemplo, `hotfix/fix-login-error`). Esta rama se crea localmente desde `trunk` y es donde se realizará todo el trabajo de desarrollo.

Durante la fase de implementación, el desarrollador realiza los cambios necesarios en el código, que pueden incluir modificaciones en modelos de datos, servicios, controladores, templates, tests, y documentación. Es fundamental que cada cambio sea acompañado de tests apropiados que verifiquen su correcto funcionamiento. El desarrollador debe probar localmente la funcionalidad, ejecutando tanto `rosemary test` para verificar que no se han roto tests existentes y que los nuevos tests pasan, como pruebas manuales para validar el comportamiento desde la perspectiva del usuario.

Cuando el desarrollador está satisfecho con los cambios, realiza un commit siguiendo la **Conventional Commits specification** establecida en el Acuerdo 2025-02-01. El mensaje debe comenzar con un tipo (`feat:` para nuevas funcionalidades, `fix:` para correcciones, `test:` para tests, `docs:` para documentación, `refactor:` para refactorizaciones, etc.), seguido de una descripción concisa del cambio. Si el commit introduce un breaking change que rompe la compatibilidad con versiones anteriores, se añade un signo de exclamación después del tipo (`feat!:`). Por ejemplo: `feat: add country filter to homepage search` o `fix!: change PublicationType enum values`.

Es crucial entender que en nuestro flujo de trabajo **no utilizamos Pull Requests**. En su lugar, el merge se realiza localmente mediante la línea de comandos. Una vez completados los cambios en la rama feature, el desarrollador cambia a la rama `trunk` (`git checkout trunk`), la actualiza (`git pull origin trunk`) y realiza el merge sin fast-forward (`git merge --no-ff feature/add-country-filter`). Esta opción `--no-ff` es importante porque crea un commit de merge explícito, preservando la historia de que el trabajo se realizó en una rama separada y facilitando la reversión completa de la funcionalidad si fuera necesario.

En el momento del commit a `trunk`, se activan los **Git hooks** configurados en el proyecto. Estos hooks ejecutan automáticamente el commit spell checker para validar el formato del mensaje, Pylint para verificar la calidad del código, y Pytest para ejecutar todos los tests. Si alguna de estas verificaciones falla, el commit es rechazado y el desarrollador debe corregir los problemas antes de poder continuar. Este mecanismo actúa como una primera línea de defensa, evitando que código de baja calidad o con bugs conocidos llegue a la rama principal.

Una vez que el commit a `trunk` es exitoso, el desarrollador pushea los cambios al repositorio remoto (`git push origin trunk`). Esto dispara automáticamente el pipeline de **GitHub Actions**, que las verificaciones en un entorno limpio y controlado. Si todas las verificaciones pasan, el código está listo para ser promovido a `main`.

La actualización de `main` se realiza con frecuencia (típicamente varias veces por semana) mediante un merge de `trunk` a `main` (`git checkout main`, `git pull origin main`, `git merge --no-ff trunk`, `git push origin main`). Este push a `main` activa automáticamente el despliegue en el entorno de desarrollo en Render.

Cuando el equipo decide que los cambios en desarrollo están listos para los usuarios finales, se realiza un despliegue a producción. Render detecta automáticamente el cambio en la rama `main` y ejecuta el proceso de build y despliegue utilizando Docker. Durante este proceso, se construye la imagen Docker según las especificaciones del `Dockerfile`, se ejecutan las migraciones de base de datos pendientes con Alembic, y finalmente se reemplaza la versión anterior de la aplicación por la nueva, con un breve período de inactividad minimizado gracias a las capacidades de rolling deployment de Render.

Tras la integración exitosa, el desarrollador puede eliminar la rama feature tanto localmente (`git branch -d feature/add-country-filter`) como remotamente si fue pusheada (`git push origin --delete feature/add-country-filter`), manteniendo así el repositorio limpio. Finalmente, la issue correspondiente se marca como "Done" en GitHub Projects y se cierra, completando el ciclo.

### Ejemplo práctico: Añadir nuevas opciones al enum PublicationType

Para ilustrar el proceso completo con un caso concreto, consideremos la siguiente necesidad: un usuario ha solicitado la capacidad de clasificar los datasets de coches con estados adicionales relacionados con inspecciones técnicas. Actualmente, el enum `PublicationType` incluye valores como "Available to Buy", "Sold", "Missing", etc., pero no contempla estados como "Pending ITV" (pendiente de inspección técnica) o "ITV Failed" (no pasó la inspección).

**Fase 1: Planificación y creación de la issue**

El Product Owner o cualquier miembro del equipo crea una issue en GitHub titulada "Add ITV-related states to PublicationType enum". En la descripción se incluye:

- **Contexto**: Los usuarios necesitan clasificar vehículos según su estado de inspección técnica, ya que esto afecta significativamente su valor y disponibilidad en el mercado.
- **Solución propuesta**: Añadir dos nuevos valores al enum PublicationType: `pending_itv` y `itv_failed`. Esto requiere modificar el modelo de datos, actualizar las migraciones de base de datos, adaptar los formularios de creación/edición de datasets, y añadir estas opciones en los filtros de búsqueda.
- **Asignados**: Carlos Palmas Santos (implementación), Javier Milá de la roca (revisión de código)
- **Etiquetas**: `enhancement`, `backend`, `frontend`

La issue se añade al backlog en GitHub Projects y se prioriza para el siguiente sprint. Cuando Carlos comienza a trabajar en ella, mueve la tarjeta a "In Progress".

**Fase 2: Preparación del entorno**

Carlos abre Visual Studio Code, asegura que su repositorio esté sincronizado (`git pull origin trunk`) y crea una nueva rama local:

```bash
git checkout -b feature/add-itv-publication-types
```

**Fase 3: Implementación**

La implementación requiere cambios en múltiples capas de la aplicación:

1. **Modelos de datos** (`app/modules/dataset/models.py`): Se añaden los nuevos valores al enum:
```python
class PublicationType(Enum):
    # ... valores existentes ...
    PENDING_ITV = "pending_itv"
    ITV_FAILED = "itv_failed"
```

2. **Migración de base de datos**: Se crea una nueva migración con Alembic que modifica la columna del enum para incluir los nuevos valores, asegurando que los datos existentes no se vean afectados.

3. **Formularios** (`app/modules/dataset/forms.py` y templates): Se actualizan los selectores de tipo de publicación en los formularios de creación y edición de datasets para incluir las nuevas opciones.

4. **Tests**: Se añaden tests que verifican que los nuevos valores del enum se pueden asignar correctamente, que aparecen en los formularios, y que la búsqueda y filtrado funcionan con estos nuevos estados.

Durante el desarrollo, Carlos ejecuta periódicamente `rosemary test` para verificar que no está rompiendo funcionalidad existente. También prueba manualmente creando un dataset con el nuevo tipo de publicación y verificando que se muestra correctamente en la interfaz.

**Fase 4: Commit y validación local**

Una vez satisfecho con los cambios, Carlos realiza un commit con un mensaje descriptivo:

```bash
git add .
git commit -m "feat: add ITV-related states to PublicationType enum

- Add PENDING_ITV and ITV_FAILED to PublicationType enum
- Create Alembic migration for database schema update
- Update forms and templates to include new options
- Add comprehensive tests for new publication types"
```

Los Git hooks se ejecutan automáticamente, verificando el formato del mensaje de commit, ejecutando Pylint y Pytest. Todas las verificaciones pasan exitosamente.

**Fase 5: Integración en trunk**

Carlos cambia a la rama trunk, la actualiza, y realiza el merge:

```bash
git checkout trunk
git pull origin trunk
git merge --no-ff feature/add-itv-publication-types
```

El merge se completa sin conflictos. Carlos pushea a trunk:

```bash
git push origin trunk
```

**Fase 6: Revisión de código**

Javier, el revisor asignado, recibe una notificación (a través de GitHub o del sistema de comunicación del equipo). Revisa los cambios directamente en GitHub o haciendo checkout de trunk localmente, verificando:

- La calidad del código y adherencia a los estándares del proyecto
- La completitud de los tests
- La correcta documentación de los cambios
- Que la migración de base de datos es segura y reversible

Si Javier encuentra problemas, los comunica a Carlos (por ejemplo, mediante comentarios en la issue). Carlos crearía entonces un nuevo commit de corrección en trunk directamente o en una nueva rama feature si los cambios son sustanciales. En este caso, Javier aprueba los cambios sin observaciones.

**Fase 7: Promoción a main y despliegue**

El equipo decide que trunk está estable y listo para producción. Carlos (o cualquier miembro autorizado) realiza el merge a main:

```bash
git checkout main
git pull origin main
git merge --no-ff trunk
git push origin main
```

Este push a main activa dos eventos en cadena:

1. **GitHub Actions** ejecuta el pipeline completo de CI: validación, linting, tests completos.
2. **Render** detecta el cambio en main y comienza el proceso de despliegue:
   - Clona el repositorio
   - Construye la imagen Docker
   - Ejecuta `alembic upgrade head` para aplicar la migración
   - Despliega los contenedores actualizados
   - Realiza health checks para verificar que la aplicación arrancó correctamente

**Fase 8: Verificación en producción y cierre**

Una vez desplegado, Carlos verifica en el entorno de producción que:
- Los nuevos tipos de publicación aparecen en los formularios
- Se pueden crear datasets con estos tipos
- Los filtros de búsqueda funcionan correctamente
- No hay errores en los logs de Render

Satisfecho con el resultado, Carlos elimina la rama feature:

```bash
git branch -d feature/add-itv-publication-types
```

Finalmente, actualiza la issue en GitHub Projects moviéndola a "Done" y cierra la issue con un comentario que resume lo implementado y proporciona el commit hash para referencia futura.

Este ciclo completo, desde la identificación de la necesidad hasta el código en producción, ejemplifica cómo nuestro proceso integra metodología ágil, control de versiones riguroso, testing automatizado y despliegue continuo para entregar valor de forma rápida y confiable.

## Entorno de desarrollo

### Sistemas Operativos y Herramientas

El entorno de desarrollo ha sido diseñado para ser agnóstico del sistema operativo anfitrión, estandarizando sobre un entorno **Linux (Ubuntu 22.04 LTS "Jammy Jellyfish")** mediante el uso de virtualización y contenedorización. Gracias a la virtualización, los miembros del equipo pueden trabajar en entornos idénticos.

**Herramientas Principales:**

*   **Docker & Docker Compose:** Herramienta fundamental para la orquestación de servicios. Encapsula la aplicación, la base de datos (MariaDB) y otros servicios (Mailhog) en contenedores aislados.
*   **Vagrant:** Utilizado alternativamente para aprovisionar una máquina virtual completa con todas las dependencias preinstaladas.
*   **Git:** Control de versiones distribuido.
*   **Visual Studio Code:** IDE recomendado, configurado con extensiones para Python y Docker.

### Lenguajes, Frameworks y Dependencias

El núcleo del desarrollo se basa en **Python 3**, utilizando un entorno virtual (`venv`) para aislar las librerías del proyecto.

**Dependencias Clave (según `requirements.txt`):**

*   **Framework Web:** `Flask==3.1.1` (con extensiones como `Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-Login`).
*   **Base de Datos:** `SQLAlchemy` como ORM y `PyMySQL` como driver.
*   **Pruebas:** `pytest`, `pytest-cov`, `selenium` (para pruebas E2E).
*   **Utilidades:** `python-dotenv` (manejo de configuración), `Faker` (generación de datos de prueba).
*   **Calidad de Código:** `black`, `flake8`, `pre-commit` (para asegurar estilo antes de cada commit).

### Instalación y Ejecución

Para facilitar la incorporación de nuevos desarrolladores, se han habilitado dos vías principales de despliegue local:

#### Opción A: Despliegue con Docker 

Este método levanta todo el stack tecnológico en contenedores, requiriendo únicamente tener Docker instalado.

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/coche-hub/coche-hub.git
    cd coche-hub
    ```
2.  **Configurar variables de entorno:**
    Copiar el fichero de ejemplo:
    ```bash
    cp .env.local.example .env
    ```
3.  **Ejecutar el sistema:**
    ```bash
   docker compose -f docker/docker-compose.dev.yml up -d 
    ```
    El sistema estará disponible en `http://localhost:5000`.

#### Opción B: Entorno Virtual (Vagrant)

Para quienes prefieren una máquina virtual pre-aprovisionada con Ansible:

1.  Instalar Vagrant y VirtualBox.
2.  Configurar variables de entorno:
    cp .env.vagrant.example .env
3.  cd vagrant
4.  Ejecutar `vagrant up`.


#### Opción C: Entorno Local

Para quienes prefieren una máquina virtual pre-aprovisionada con Ansible:

1. Clona el proyecto
cd coche-hub
2. Install and configure MariaDB
sudo apt install mariadb-server -y
sudo systemctl start mariadb
sudo mysql_secure_installation
- Enter current password for root (enter for none): (enter)
- Switch to unix_socket authentication [Y/n]: `y`
- Change the root password? [Y/n]: `y`
    - New password: `cochehubdb_root_password`
    - Re-enter new password: `cochehubdb_root_password`
- Remove anonymous users? [Y/n]: `y`
- Disallow root login remotely? [Y/n]: `y` 
- Remove test database and access to it? [Y/n]: `y`
- Reload privilege tables now? [Y/n] : `y`
sudo mysql -u root -p
CREATE DATABASE cochehubdb;
CREATE DATABASE cochehubdb_test;
CREATE USER 'cochehubdb_user'@'localhost' IDENTIFIED BY 'cochehubdb_password';
GRANT ALL PRIVILEGES ON cochehubdb.* TO 'cochehubdb_user'@'localhost';
GRANT ALL PRIVILEGES ON cochehubdb_test.* TO 'cochehubdb_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
3. Configurar las variables de entorno:
cp .env.local.example .env
echo "webhook" > .moduleignore
4. Ejecutar el sistema:
sudo apt install python3.12-venv
python3.12 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e ./
rosemary
flask db upgrade
rosemary db:seed
flask run --host=0.0.0.0 --reload --debug


### Diferencias de Entorno

Gracias a la estandarización con Docker, **no existen diferencias significativas** en el entorno de ejecución entre los miembros del equipo. Las únicas variaciones se limitan a las herramientas de edición de código (IDE) ,pero la capa de ejecución (Runtime, DB, librerías) es idéntica para todos, eliminando el clásico problema de "en mi máquina funciona".

---

## Ejercicio de propuesta de cambio

Para ilustrar el flujo de trabajo de *Evolución y Gestión de la Configuración* seguido en el proyecto, simularemos la implementación de un cambio sencillo: **Añadir un enlace de "Soporte" en el pie de página (footer) de la aplicación.**

A continuación se detalla el proceso paso a paso:

### 1. Propuesta (Gestión de Incidencias)
El proceso comienza con la identificación de la necesidad.
*   **Acción:** Crear una *Issue* en GitHub.

### 2. Análisis y Creación de Rama (Gestión de Configuración)
El desarrollador asignado crea una rama específica para aislar el desarrollo.
*   **Comando:**
    ```bash
    git fetch 
    git checkout -b feature/add-support-link
    ```
*   **Explicación:** Se basa en la rama `trunk` y sigue la convención de nombres: `tipo/nombre`.

### 3. Implementación (Desarrollo)
El desarrollador realiza los cambios en el código.
*   **Archivo modificado:** `app/templates/base/footer.html` (ruta hipotética).
*   **Cambio de código:**
    ```html
    <!-- Antes -->
    <footer>&copy; 2025 Coche-hub</footer>

    <!-- Después -->
    <footer>
        &copy; 2025 Coche-hub | <a href="mailto:support@cochehub.io">Soporte</a>
    </footer>
    ```
*   **Verificación Local:** El desarrollador ejecuta la aplicación y verifica visualmente que el enlace aparece y funciona.

### 4. Control de Cambios (Commits)
Se registran los cambios utilizando *Conventional Commits*.
*   **Comandos:**
    ```bash
    git add app/templates/base/footer.html
    git commit -m "feat: add support link to page footer "
    git checkout trunk
    git merge feature/add-support-link --no-ff
    git push 
    ```
*   **Herramienta:** Git CLI.

### 5. Integración y Despliegue 
Se merge la rama trunk en main

Este ciclo cierra el flujo de evolución, garantizando trazabilidad desde la solicitud inicial hasta el código desplegado.

---

## Conclusiones y trabajo futuro

### Conclusiones Principales

El proyecto **Coche-hub** ha sido un éxito tanto en su vertiente técnica como en la metodológica. Se ha logrado transformar un prototipo académico en una plataforma robusta, escalable y mantenible.

Las principales conclusiones derivadas de este trabajo son:

1.  **Arquitectura Sólida:** La adopción del patrón **Monolito Modular** ha demostrado ser la elección correcta. Ha permitido a los desarrolladores trabajar con la independencia de los microservicios, pero sin la sobrecarga operativa inherente a los sistemas distribuidos.
2.  **Cultura de Calidad:** La integración de pruebas automatizadas y pipelines de CI/CD ha evitado la acumulación de deuda técnica. 
3.  **Gestión del Caos:** A través de una gestión estricta de ramas, se ha coordinado el trabajo de seis personas sobre el mismo repositorio sin conflictos bloqueantes, validando las prácticas de Gestión de Configuración.
4.  **Valor para el Usuario:** Más allá de la tecnología, se ha entregado valor real: la comunidad de investigación ahora tiene herramientas poderosas para compartir y descubrir datos.

### Aprendizajes Obtenidos

El equipo ha adquirido competencias críticas en ingeniería de software moderna:

*   **Docker es indispensable:** La contenedorización ha eliminado los problemas de compatibilidad entre entornos locales de Windows y Linux.
*   **La comunicación es código:** Los mensajes de commit claros (Conventional Commits) y las ramas con nombres clarosson tan importantes como el código Python en sí mismo para mantener el proyecto mantenible.
*   **Testing como documentación:** Los tests bien escritos sirven como la mejor documentación viva de cómo debe comportarse el sistema.

### Limitaciones Encontradas

A pesar del éxito, se han identificado ciertas limitaciones:

*   **Dependencia de Terceros:** La integración profunda con Zenodo crea una dependencia externa. Si la API de Zenodo cambia o cae, la funcionalidad de subida de Coche-hub se ve afectada. (Mitigado  con `fakenodo`).


### Trabajo Futuro

Para futuras iteraciones del proyecto, se proponen las siguientes líneas de trabajo que no han sido abordadas en esta entrega:


2.  **Internacionalización (i18n):** Implementar soporte multi-idioma (Español/Inglés) utilizando *Flask-Babel*, para ampliar el alcance de la plataforma a la comunidad internacional.
3.  **Funcionalidades Sociales:** Añadir capacidades de red social, como perfiles de usuario públicos, comentarios en datasets y valoraciones (estrellas), para fomentar la interacción comunitaria.
4.  **API Pública:** Exponer una API RESTful documentada (Swagger/OpenAPI) para que otros desarrolladores puedan construir herramientas sobre los datos de Coche-hub.
