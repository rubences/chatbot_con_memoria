---
fuente_pdf: v0_by_Vercel.pdf
ruta_origen: /workspaces/chatbot_con_memoria/contexto/modulo5-main/modulo5-main/v0_by_Vercel.pdf
temas: ia
origen: llamacloud
---

# Documento: v0_by_Vercel.pdf

## Fuente

Parseado con LlamaCloud y almacenado para recuperación RAG.

## Markdown

# v0 by Vercel

## Diseño de interfaces y Frontend a la velocidad del pensamiento

> Natural text description
> nicetend a la velocidad del
> pensamiento

Module: Desarrollo Avanzado de Sistemas Multiagente

**Instructor**: Rubén Juárez Cádiz

![Abstract digital interface with code snippets and UI elements](page_1_image_1_v2.jpg)

---

# ¿Qué aprenderemos hoy?

1. El cuello de botella del Frontend: el tiempo perdido en maquetación

2. ¿Qué es el Diseño Generativo (Generative UI)?

3. ¿Qué es v0 y por qué es diferente?

4. Prompting Visual: cómo describir interfaces

5. Iteración por Bloques: modificar sin regenerar

6. Exportación: del No-Code al Pro-Code

7. Caso práctico: Dashboard de un SaaS de IA

9. Exportación del código React

10. Entregable y criterios de evaluación

11. Próximos pasos y recursos

---

# Pasar de una idea a código funcional consume días. v0 lo reduce a minutos.

## El Cuello de Botella del Frontend

![Infografía del flujo tradicional de desarrollo frontend que muestra un embudo de procesos: Wireframe (4-8 horas), Maquetación HTML/CSS (1-3 días), Componentización React (1-2 días), y Responsive y accesibilidad (4-8 horas), sumando un total de 3-6 días.](page_3_image_1_v2.jpg)

### El problema

El tiempo de maquetación es tiempo que no se invierte en lógica de negocio o IA.

![Cuadro destacado con el texto "La promesa de v0: Reducir el ciclo completo a menos de 30 minutos." acompañado de iconos de código y velocidad.](page_3_image_2_v2.jpg)

---

# v0 no genera imágenes de webs; genera código React real, accesible y listo para producción

## ¿Qué es el Diseño Generativo?

### **Diseño Generativo** (Generative UI)

* LLMs entrenados en código web generan componentes UI desde lenguaje natural.

* Tecnologías que genera v0: React, Tailwind CSS, shadcn/ui, TypeScript.

![Diagram showing the process from natural text to v0, then to React code, and finally to a visual component.](page_4_image_1_v2.jpg)

<table>
  <thead>
    <tr>
        <th> </th>
        <th>Midjourney/DALL-E</th>
        <th>Figma</th>
        <th>v0 by Vercel</th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td>Output:</td>
<td>Imagen PNG</td>
<td>Archivo vectorial</td>
<td>Código React +<br/>Tailwind CSS</td>
    </tr>
<tr>
        <td>Producción:</td>
<td>No usable en producción</td>
<td>No usable directamente</td>
<td>Sí, directamente</td>
    </tr>
  </tbody>
</table>



---

# Un buen prompt visual describe el layout, los componentes y el comportamiento esperado
Prompting Visual: El Arte de Describir Interfaces

## Nivel 1 — Layout (Estructura):
Un panel lateral a la izquierda con navegación, área principal a la derecha con 3 tarjetas de métricas en la parte superior y una tabla de datos debajo.

![Esquema de layout con sidebar y panel principal con métricas y tabla](page_5_image_1_v2.jpg)

## Nivel 2 — Componentes (Detalle):
Las tarjetas de métricas deben mostrar un número grande, un título descriptivo, y un indicador de tendencia (flecha verde hacia arriba o roja hacia abajo).

![Tres tarjetas de métricas mostrando los valores 65, 3,106 y 129 con sus respectivos indicadores de tendencia](page_5_image_4_v2.jpg)

## Nivel 3 — Estilo y Comportamiento:
Tema oscuro. Sidebar colapsable con iconos. Hover effects suaves en las filas de la tabla. Usa Tailwind y shadcn/ui.

![Interfaz de usuario en modo oscuro con logotipos de tailwindcss y shadcn/ui](page_5_image_2_v2.jpg)

> **Regla de oro:** Piensa como un diseñador describiendo su trabajo a un desarrollador: sé específico en la estructura, los datos y el comportamiento interactivo.

---

# La iteración selectiva es lo que convierte v0 en una herramienta de diseño profesional

## Iteración por Bloques: Modificar sin Regenerar

### El problema:
Regenerar toda la página pierde el contexto de lo que ya funcionaba.

### La solución:
Seleccionar un componente específico y darle instrucciones precisas.

**Ejemplo 1:** [Botón "Guardar"] -> "Haz este botón más grande, rojo peligro, con icono de advertencia." ⚠️

**Ejemplo 2:** [Tabla de usuarios] -> "Añade 👥✅ avatares, badge de estado y filas alternadas." 📑

![Infografía que muestra el proceso de iteración selectiva en v0. A la derecha, una interfaz de usuario con un botón "GUARDAR" seleccionado. Un cuadro de diálogo de instrucciones dice: "Instrucciones: Haz este botón más grande, rojo peligro, con icono de advertencia." Debajo se muestra una comparación "ANTES" con un botón azul pequeño y "DESPUÉS" con un botón rojo grande que incluye un icono de advertencia.](page_6_image_2_v2.jpg)

---

# v0 es el punto de partida; la exportación es el puente hacia el proyecto real

### Exportación: Del No-Code al Pro-Code

![Diagrama de flujo del proceso de exportación](page_7_image_3_v2.jpg)

**Diseño en v0 (No-Code)**
→ Iterar hasta obtener la interfaz deseada

**"Open in v0" / Fork**
→ Crear una copia editable del proyecto

**Copy Code**
→ Copiar el código React del componente

**Integrar en Next.js / React**
→ Pegar en `/components/Dashboard.tsx`

**Conectar con la lógica real**
→ Reemplazar datos simulados con llamadas a la API

**Lo que obtienes al exportar:**

* [x] - Componentes React modulares y reutilizables
* [x] - Código Tailwind CSS limpio y sin clases redundantes
* [x] - Componentes accesibles (ARIA labels, keyboard navigation)
* [x] - Tipado TypeScript incluido

> **Importante:** v0 genera el "esqueleto" visual. La lógica de negocio siempre la añade el desarrollador.

---

# Prototipado del Dashboard de nuestro SaaS de IA sin escribir una sola línea de CSS
Caso Práctico: Dashboard del SaaS de IA

**Key Points:**

* **El reto:** Crear la interfaz completa de un panel de control para una herramienta de IA, sin escribir código CSS, en menos de 30 minutos.

```description
El prompt base (Paso 1):

Crea un dashboard de administración moderno con tema oscuro.
Sidebar colapsable a la izquierda con iconos y etiquetas: Dashboard, Agentes, Conversaciones, Métricas, Configuración.
Área principal con:
- Header con nombre del proyecto y avatar de usuario
- 3 tarjetas de métricas: 'Agentes Activos', 'Conversaciones Hoy', 'Coste Total ($)'
- Un gráfico de líneas simulado de 'Uso de tokens por día'
- Una tabla de 'Últimas conversaciones' con columnas: Usuario, Agente, Duración, Estado, Fecha
- Usa Tailwind CSS y shadcn/ui.
Diseño responsive.
```

```description
La iteración selectiva (Paso 2):

[Seleccionar la tabla de conversaciones]
"Añade avatares de usuario en la primera columna, un badge de color para el Estado (verde=Completada, amarillo=En progreso, rojo=Error), y un botón de 'Ver detalle' en cada fila."
```

![Dashboard de administración moderno con tema oscuro que incluye una barra lateral de navegación, tarjetas de métricas para Agentes Activos (15), Conversaciones Hoy (256) y Coste Total ($1,450), un gráfico de líneas de uso de tokens por día y una tabla de últimas conversaciones con avatares, estados en color y botones de acción.](page_8_image_1_v2.jpg)

<table>
  <thead>
    <tr>
        <th>Usuario</th>
        <th>Agente</th>
        <th>Duración</th>
        <th>Estado</th>
        <th>Fecha</th>
        <th>Acción</th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td>Robdo Hoine</td>
<td>Agent Sestor</td>
<td>38 min</td>
<td>Completada</td>
<td>08/05/2023</td>
<td>Ver detalle</td>
    </tr>
<tr>
        <td>Limune lúnten</td>
<td>Ageñlenter</td>
<td>88 min</td>
<td>En progreso</td>
<td>08/05/2024</td>
<td>Ver detalle</td>
    </tr>
<tr>
        <td>Janen Sniono</td>
<td>Conversacienr</td>
<td>08 min</td>
<td>Error</td>
<td>08/05/2024</td>
<td>Ver detalle</td>
    </tr>
  </tbody>
</table>



---

# El código que genera v0 es código de producción: modular, tipado y accesible

El Código React Exportado

```typescript
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarImage } from "@/components/ui/avatar"

interface Conversation {
  user: string; agent: string; status: "Completada" | "Error"
}

export function ConversationsTable({ data }: { data: Conversation[] }) {
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader><h2 className="text-white">Últimas Conversaciones</h2></CardHeader>
      <CardContent>
        {data.map((conv) => (
          <div key={conv.user} className="flex items-center gap-4 py-2">
            <Avatar><AvatarImage src={`/avatars/${conv.user}.png`} /></Avatar>
            <span className="text-gray-300">{conv.agent}</span>
            <Badge>{conv.status}</Badge>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
```

### [Lo que hace este código]

* Componente reutilizable con TypeScript tipado

* Usa shadcn/ui para consistencia visual

* Tailwind CSS para estilos inline

* Listo para recibir datos reales de la API

---

# v0 no reemplaza al desarrollador; multiplica su velocidad de prototipado por 10x

## Comparativa: v0 vs. Métodos Tradicionales

<table>
  <thead>
    <tr>
        <th> </th>
        <th>MÉTODOS TRADICIONALES<br/>(Manual)</th>
        <th>v0<br/>(Vercel)</th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td>Tiempo hasta 1er prototipo:</td>
<td>2-3 días</td>
<td>20-30 minutos</td>
    </tr>
<tr>
        <td>Curva de aprendizaje:</td>
<td>Alta<br/>(CSS, React)</td>
<td>Baja<br/>(lenguaje natural)</td>
    </tr>
<tr>
        <td>Calidad del código:</td>
<td>Depende del dev</td>
<td>Consistente y accesible</td>
    </tr>
<tr>
        <td>Responsive por defecto:</td>
<td>Manual</td>
<td>Automático<br/>(Tailwind)</td>
    </tr>
<tr>
        <td>Iteración de diseño:</td>
<td>Lenta<br/>(editar código)</td>
<td>Rápida<br/>(prompt selectivo)</td>
    </tr>
<tr>
        <td>Integración con Next.js:</td>
<td>Nativa</td>
<td>Nativa<br/>(mismo ecosistema)</td>
    </tr>
  </tbody>
</table>

### ¿Cuándo NO usar v0?

*   ⚠️ Animaciones complejas y altamente personalizadas
*   ⚠️ Lógica de negocio compleja (v0 solo genera UI)
*   ⚠️ Diseños con identidad de marca muy específica (mejor Figma primero)

### El rol ideal de v0:

Prototipado rápido → Validación con el cliente → Exportación → Integración con la lógica del agente.

---

# Entregable y Criterios

Tu misión: Un dashboard funcional de IA prototipado y exportado en menos de 30 minutos

## Evaluation Criteria

## Required Deliverables

<table>
  <thead>
    <tr>
        <th>Criteria</th>
        <th>Weight</th>
    </tr>
  </thead>
  <tbody>
    <tr>
        <td>Prompt base (20%)</td>
<td>20%</td>
    </tr>
<tr>
        <td>Interfaz generada (25%)</td>
<td>25%</td>
    </tr>
<tr>
        <td>Iteración selectiva (20%)</td>
<td>20%</td>
    </tr>
<tr>
        <td>Código exportado (25%)</td>
<td>25%</td>
    </tr>
<tr>
        <td>Documentación (10%)</td>
<td>10%</td>
    </tr>
  </tbody>
</table>

* [x] 1. Captura del dashboard generado en v0 (antes y después de la iteración)

* [x] 2. Archivo `Dashboard.tsx` exportado e integrado en el proyecto Next.js

* [x] 3. El prompt base y el prompt de iteración documentados en un `README.md`

* [x] 4. Demostración en vivo del componente renderizado en el navegador

> **Suggested Extension:** Conectar el componente de métricas con datos reales del agente de CrewAI de la sesión anterior.



---

# Próximos Pasos y Recursos

v0 genera la interfaz. El siguiente paso es conectarla con la inteligencia de tus agentes.

*   ![v0 logo](image) **Cursor AI:** El IDE con IA integrada para conectar el código de v0 con la lógica del agente

*   ![Next.js logo](image) **Next.js + API Routes:** El backend que conecta el dashboard con los agentes de CrewAI/LangGraph

*   ![Vercel logo](image) **Vercel Deploy:** Despliegue en producción con un solo comando

## Recursos recomendados:

*   ![link icon](image) **Plataforma v0:** v0.dev (plan gratuito disponible)
*   ![document icon](image) **Documentación de shadcn/ui:** ui.shadcn.com
*   ![folder icon](image) **Repositorio del módulo en el aula virtual**

> "El mejor código es el que no tienes que escribir. V0 no te hace peor desarrollador; te libera para enfocarte en lo que realmente importa: la lógica de negocio y la inteligencia de tus agentes." — Rubén Juárez Cádiz

## Texto Plano

v0 by Vercel     Fnhyuld

    Diseño de interfaces y Frontend
                      y
                     a la velocidad del pensamiento
                     a
Naturattort deription
Natura en desccripion
Naturlat srad dad
Noran adat de            function React)
pensamiento                                              cnotes
                                                         caren utml.
                      Module: Desarrollo Avanzado de )   etst Novcot1/us
                      Sistemas Multiagente
                      Instructor: Rubén Juárez Cádiz

---

Qué aprenderemos hoy?

1. El cuello de botella del Frontend: el   6. Exportación: del No-Code al
      tiempo perdido en maquetación         Pro-Code
2. iQué es el Diseño Generativo            7. Caso práctico: Dashboard de un
      (Generative UI)?                      SaaS de IA
3. iQué es v0 y por qué es diferente?      9. Exportación del código React

4. Prompting Visual: cómo describir
4.                                         10. Entregable y criterios de
      interfaces                            evaluación
5. Iteración por Bloques: modificar sin    11. Próximos pasos y recursos
    regenerar

---

Pasar deunaidea a código funcional
    reduce a minutos.
    días. v0 lo reduce
consume días. vO
    EICuello
    Cuello de Botella del Frontend

    El flujo tradicional (sin v0)          El problema        ulhuld
              Wireframe (Figma/papel):     El tiempo de maquetación es tiempo que
              4-8 horas                    no se invierte en lógica de negocio o IA.
                                                negocio
Wl etdescription Maquetación HTML/CSS:
Natu        1-3 días
ppens  Componentización React:
               1-2 días                     La promesa de vO        .
                                                a
     Responsive y accesibilidad:            Reducir el ciclo completo a
              4-8 horas                     menos de 30 minutos.

    Total: 3-6 días

---

v0 no genera imágenes de webs; genera código
React real, accesible y listo para producción
 iQué es el Diseño Generativo?
 Diseño Generativo (Generative Ul)
  LLMs entrenados en código web generan        vo
      UI
  componentes Ul desde lenguaje natural.
               React,                      natural                React     visual
  Tecnologías que genera v0: React,
  Tailwind CSS, shadcn/ui, TypeScript.     text                   code  component

                                                                  vo
      Midjourney/DALL-E                    Figma                  v0 by Vercel

 Output:       Imagen PNG                  Archivo vectorial     Código React +
                                                                 Tailwind CSS

 Producción:   No usable en                No usable
      producción                           directamente          Sí, directamente

---

    Un
     buen prompt visual describe el layout, los
    componentesyel comportamiento esperado
    Prompting Visual: El Arte de Describir Interfaces

     Nivel 1 — Layout (Estructura):            Nivel 2 - Componentes (Detalle):             Nivel 3 - Estilo y Comportamiento:
     Un panel lateral a la izquierda con       Las tarjetas de métricas deben mostrar un    Tema oscuro. Sidebar colapsable con
     navegación, área principal a la derecha   número grande, un título descriptivo, y un   iconos. Hover effects suaves en las filas de
     con 3 tarjetas de métricas en la parte    indicador de tendencia (flecha verde         la tabla. Usa Tailwind y shadcn/ui.
     superior y una tabla de datos debajo.     hacia arriba o roja hacia abajo).

                                                       65                3,106                129
                                               Titulo descriptivo  Titulo descriptivo  Titulo descriptivo  03    t
                                                     ↑ 1.29  ↑0.55                          ↓ -1.29  *


    tailwindcss shadcn/ui



Regla de oro: Piensa como un diseñador describiendo su trabajo a un desarrollador: sé
       específico en la estructura, los datos y el comportamiento interactivo.

---

La iteración selectiva es lo que convierte v0 en una
 herramienta de diseño profesional

Iteración por Bloques: Modificar sin Regenerar

 El problema:
   Regenerar toda la página pierde el
   contexto de lo que ya funcionaba.                         Instrucciones:
                                                             Haz este botón más
                                                             peligro, con
   La solución:                                              grande, rojo
  Seleccionar un componente específico y        GUARDAR      icono de advertencia.
  darle instrucciones precisas.                              tapeiae(rrart );

 Ejemplo 1: [Botón "Guardar"] -> "Haz este botón             UPoestente/
más grande, rojo peligro, con icono de
advertencia.        GUARDAR                                  GUARDAR

Ejemplo 2: [Tabla de usuarios] -> "Añade
   2:        ->     C
avatares, badge de estado y filas alternadas."      ANTES    DESPUÉS

---

v0 es el punto de partida; la exportación es
 el puente hacia el proyecto real
     Exportación: Del No-Code al Pro-Code

Diseño en v0 (No-Code)        Lo que obtienes al exportar:
 Iterar hasta obtener la interfaz deseada   - Componentes React modulares y

"Open in vO" / Fork                        reutilizables
→ Crear una copia editable del proyecto     - Código Tailwind CsS limpio y sin clases
                                           redundantes
Copy Code                                   Componentes accesibles (ARIA labels,
 → Copiar el código React del componente    keyboard navigation)    coetob Autend1au

Integrar en Next.js / React                 - Tipado TypeScript incluido
→ Pegar en /components/Dashboard.tsx
                                             Importante: v0 genera el "esqueleto"
Conectar con la lógica real                  visual. La lógica de negocio siempre la
→ Reemplazar datos simulados con             añade el desarrollador.
 llamadas a la API

---

Prototipado del Dashboard de nuestro SaaS de IA
sin escribir una sola linea de CSS
Caso Práctico: Dashboard del SaaS de IA

Key Points:                                                                  Al SaaS Dashboard
     El reto: Crear la interfaz completa de un panel de control para una
  herramienta de IA, sin escribir código CSS, en menos de 30             0 Dashboard     Agentes Activos:             Conversaclones Hoy:
  minutos.                                                               Agenles         15                           256                           $1,450

                                                                         Conversaciones
 El prompt base (Paso 1):                                                illi Métricas   Uso de tokens por día                                          336 tokens
 Crea un dashboard de administración moderno con tema oscuro.            Configuración   1200
 Sidebar colapsable a la izquierda con iconos y etiquetas: Dashboard,                    1000
 Agentes, Conversaciones, Métricas, Configuración.                                       800
 Area principal con:                                                                     cOo
   ea ptinclpalCon
   Header con nombre del proyecto y avatar de usuario                                    400
  3 tarjetas de métricas: 'Agentes Áctivos', 'Conversaciones Hoy', 'Coste
   Total ($)                                                                             20
  Un gráfico de líneas simulado de 'Uso de tokens por día'
  Una tabla de 'Ultimas conversaciones' con columnas: Usuario, Agente                    00/08    02/28         09/30     03/11     05/10 07/13     05/19     05/21 31/13
   Duración, Estado, Fecha
   unacion,Lstaao,
  Usa Tailwind CSS y shadcn/ui.
 Diseño responsive.                                                                      Ultimas conversaciones
                                                                                         Usuario            Agente          Duración Estado         Fecha

                                                                                             Robda Hoine                    38 min     Completada   08/05/2023     r detalle

 La iteración selectiva (Paso 2):                                                            Limune lúnten                  68 min                  08/05/2024 Ver detalle

 [Seleccionar la tabla de conversaciones]                                                                   Conversacienr   08 min                  08/05/2024
   'Añade avatares de usuario en la primera columna, un badge de color para
 el Estado (verde=Completada, amarillo=En progreso, rojo=Error), y un
 botón de 'Ver detalle' en cada fila.'

---

El códigoquegenera v0 es código de
tipado y accesible
producción: modular,
modular, t
Código
El Código React Exportado


import{Card, CardContent, CardHeader } from
import  Badge } from "@/components/ui/badge""@/components/ui/card"        [Lo que hace este código]
     {
import { Avatar, AvatarImage } from "@/components/ui/avatar"
interface Conversation {                                              TypeScript tipado
user: string; agent: string; status: "Completada" "Error"                                   Componente reutilizable

export function ConversationsTable({ data }: { data: Conversation[] }) {                    con TypeScript tipado
return                                                                Tailwind CSS inline   Usa shadcn/ui para
<Card className="bg-gray-900 border-gray-800">
 <CardHeader><h2 className="text-white">últimas Conversaciones</h2></CardHeader>            consistencia visual
 <CardContent>
        {data.map((conv) => (
         <div key={conv.user} className="flex items-center gap-4 py-2">                      Tailwind CSS para estilos
               <Avatar><AvatarImage src={'/avatars/${conv.user}.png'} /></Avatar>
               <span className="text-gray-300">{conv.agent}</span>                          inline
               <Badge>{conv.status}</Badge>
         </div>
        ))}                                                           Usa shadcn/ui          Listo para recibir datos
 </CardContent>
</Card>                                                                                      reales de la API

---

v0 no reemplaza al desarrollador; multiplica su
velocidad de prototipado por 10x
Comparativa: vO vs. Métodos Tradicionales

               MÉTODOS TRADICIONALES       vo                 Cuándo NO usar vO?

 Tiempo hasta      (Manual)             (Vercel)               Animaciones complejas y
 1er prototipo:    2-3 días             20-30 minutos         altamente personalizadas
 Curva de          Alta                 Baja                   Lógica de negocio compleja (v0
                                                              solo genera UI)
 aprendizaje:      (CSS, React)         (lenguaje natural)     UI)
                                                               Diseños con identidad
 Calidad del                            Consistente y      muy específicaidentidad deᵐᵃʳᶜᵃ
 codigo:             Depende del dev    accesible             muy específica (mejor Figma primero)
                                                                   mnec(t')
 Responsive por    Manual               Automático
 defecto:                               (Tailwind)            El rol ideal de vO:
 Iteración de      Lenta                Rápida                Prototipado rápido → Validación con
 diseño:           (editar código)      (prompt selectivo)    el cliente → Exportación
 Integración con   Nativa      NEXT     Nativa                Integración con la lógica del agente.
 Next.js:
                                        (mismo ecosistema)

---

    Entregable y Criterios
Tu misión: Un dashboard funcional de IA prototipado y
                                     30minutos
              exportado en menos de 30 minutos
Evaluation Criteria               Required
                                       Deliverables
Prompt base (20%)             20%    1.
                                     1. Captura del dashboard generado en v0
                                     (antes y después de la iteración)
                                       ydespués
                                     2.
Interfaz generada (25%)       25%    2. Archivo Dashboard.tsx exportado e
                                     integrado en el proyecto Next.js
                                  3.
                                     3. El prompt base y el prompt de iteración
                                         y
Iteración selectiva (20%)     20%        yel prompt de iteración
                                     documentados en un README.md
                                     4. Demostración en vivo del componente
                                     4.
Código exportado (25%)        25%    renderizado en el navegador

Documentación (10%)           10%    SuggestedExtension: Conectar el componente
                                  de métricascondatos reales del agente de
                                         agente
                                  CrewAl de la sesión anterior.

---

                                         Próximos Pasos y Recursos
                                                  Pasos y
v0 genera la interfaz. El siguiente paso es conectarla con la inteligencia de tus agentes.

 vo                   Cursor Al: El IDE con IA integrada para conectar el código de v0
                      lógicadelagente
                      con la
                      con la lógica del agente
                                         Next.js + APl Routes: El backend que conecta el dashboard
                                       N Next.js
                                         con los API Routes:
                                         con los agentes de CrewAl/LangGraph

     NEXT.s                                      Vercel Deploy: Despliegue en producción con un
                                                 solo comando
Recursos recomendados:
     (plan
Plataforma v0: v0.dev (plan gratuito disponible)
Documentación de shadcn/ui: ui.shadcn.com
Repositorio del módulo en el aula virtual

 "El mejor
 código   e
     que no
 "El mejor código es el que no tienes que escribir. V0 no te hace peor desarrollador; te libera para enfocarte
 en lo que realmente importa: la lógica de negocio y la inteligencia de tus agentes." — Rubén Juárez Cádiz