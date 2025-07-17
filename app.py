import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random
from google.oauth2 import service_account
from googleapiclient.discovery import build
import openai
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Innovation Hub - Análisis de Iniciativas",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS mejorados
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        color: white;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .initiative-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .initiative-card:hover {
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        transform: translateX(5px);
    }
    
    .header-gradient {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    .css-1d391kg {
        background: white;
        border-radius: 15px;
        padding: 1rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        border-radius: 15px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 25px;
        background: transparent;
        border-radius: 10px;
        color: #667eea;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    div[data-testid="metric-container"] {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 2px solid #667eea;
    }
    
    div[data-testid="metric-container"] > div {
        color: #667eea;
    }
    
    .quick-win-badge {
        background: #10b981;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
    }
    
    .strategic-badge {
        background: #f59e0b;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
    }
    
    .high-risk-badge {
        background: #ef4444;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Header con gradiente
st.markdown("""
<div class="header-gradient">
    <h1 style="margin: 0; font-size: 3rem;">🚀 Innovation Hub</h1>
    <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">Sistema Inteligente de Análisis de Iniciativas</p>
</div>
""", unsafe_allow_html=True)

# Sidebar mejorada
with st.sidebar:
    st.markdown("""
    <div style="background: white; padding: 20px; border-radius: 15px; margin-bottom: 20px;">
        <h2 style="color: #667eea; margin: 0;">⚙️ Panel de Control</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # API Keys
    with st.expander("🔑 Configuración de APIs", expanded=False):
        openai_api_key = st.text_input("OpenAI API Key", type="password", help="Ingresa tu clave API de OpenAI para análisis avanzado")
    
    # Google Sheets Configuration
    with st.expander("📊 Google Sheets", expanded=False):
        spreadsheet_id = st.text_input("ID de la hoja de cálculo", help="Encuentra el ID en la URL de tu Google Sheet")
        sheet_name = st.text_input("Nombre de la hoja", value="Respuestas")
    
    # Opciones de visualización
    st.markdown("### 🎨 Opciones de Visualización")
    use_demo_data = st.checkbox("Usar datos de demostración", value=True)
    show_animations = st.checkbox("Mostrar animaciones", value=True)
    theme_color = st.selectbox("Tema de color", ["Púrpura", "Azul", "Verde", "Naranja"])
    
    # Filtros rápidos
    st.markdown("### 🔍 Filtros Rápidos")
    quick_filter = st.radio("Mostrar:", ["Todas", "Quick Wins", "Estratégicas", "Alto Riesgo"])
    
    # Botón de actualización
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.rerun()

# Funciones auxiliares
def generate_extended_demo_data():
    """Genera 50+ datos de demostración más realistas"""
    
    # Listas expandidas para mayor variedad
    nombres = [
        'Ana García', 'Carlos López', 'María Rodríguez', 'Juan Pérez', 'Laura Martínez',
        'Pedro Sánchez', 'Sofia Hernández', 'Diego Torres', 'Carmen Ruiz', 'Andrés Morales',
        'Patricia Jiménez', 'Roberto Silva', 'Elena Vargas', 'Miguel Castro', 'Isabel Ramos',
        'Fernando Ortiz', 'Lucía Mendoza', 'Alejandro Reyes', 'Natalia Guerrero', 'Ricardo Flores',
        'Daniela Aguilar', 'Jorge Medina', 'Valeria Cruz', 'Sebastián Rojas', 'Camila Herrera',
        'Martín Díaz', 'Adriana Salazar', 'Emilio Vega', 'Paula Navarro', 'Gabriel Campos',
        'Mónica Paredes', 'Héctor Luna', 'Claudia Ríos', 'Raúl Peña', 'Andrea Sandoval',
        'Luis Cervantes', 'Beatriz Maldonado', 'Oscar Delgado', 'Mariana Espinoza', 'Iván Zamora',
        'Silvia Cortés', 'Arturo Méndez', 'Rosa Guzmán', 'Víctor Rosales', 'Teresa Pacheco',
        'Manuel Ibarra', 'Alicia Núñez', 'Rodrigo Serrano', 'Verónica Mora', 'Francisco Valdez',
        'Diana Ramírez', 'Gustavo León'
    ]
    
    departamentos = ['IT', 'Ventas', 'Marketing', 'RRHH', 'Finanzas', 'Operaciones', 'Innovación', 
                    'Calidad', 'Legal', 'Compras', 'Logística', 'Servicio al Cliente']
    
    # Generar fechas distribuidas en los últimos 30 días
    base_date = datetime.now() - timedelta(days=30)
    timestamps = []
    for i in range(52):
        random_days = random.uniform(0, 30)
        random_hours = random.uniform(8, 18)
        timestamp = base_date + timedelta(days=random_days, hours=random_hours)
        timestamps.append(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
    
    iniciativas = [
        {
            'titulo': 'CRM inteligente con IA para predicción de ventas',
            'descripcion': 'Implementar un CRM que use IA para predecir qué clientes tienen mayor probabilidad de compra',
            'beneficios': 'Aumento del 30% en conversión de ventas',
            'recursos': 'Licencias de IA, 2 desarrolladores, 3 meses',
            'tiempo': '3 meses',
            'presupuesto': '$35,000'
        },
        {
            'titulo': 'Sistema de voz del cliente con análisis semántico',
            'descripcion': 'Analizar feedback de clientes para insights accionables',
            'beneficios': 'Mejora del 25% en satisfacción del cliente',
            'recursos': 'Herramientas de text mining, analista CX',
            'tiempo': '2 meses',
            'presupuesto': '$22,000'
        },
        {
            'titulo': 'Plataforma de innovación social corporativa',
            'descripcion': 'Proyectos de impacto social liderados por empleados',
            'beneficios': 'Mejora del 50% en engagement y propósito',
            'recursos': 'Coordinador de RSE, presupuesto para proyectos',
            'tiempo': '4 meses',
            'presupuesto': '$30,000'
        },
        {
            'titulo': 'Sistema de gestión de talento con IA',
            'descripcion': 'Identificar y desarrollar alto potencial automáticamente',
            'beneficios': 'Retención del 90% de talento clave',
            'recursos': 'Plataforma de talent analytics, consultor RRHH',
            'tiempo': '3 meses',
            'presupuesto': '$45,000'
        },
        {
            'titulo': 'Hub de innovación abierta',
            'descripcion': 'Espacio físico para colaboración con startups y partners',
            'beneficios': 'Aceleración 3x en desarrollo de innovaciones',
            'recursos': 'Espacio, mobiliario, coordinador de innovación',
            'tiempo': '5 meses',
            'presupuesto': '$75,000'
        }
    ]
    
    # Generar dataset completo
    data_rows = []
    for i in range(52):
        row = {
            'Timestamp': timestamps[i],
            'Nombre': nombres[i % len(nombres)],
            'Departamento': random.choice(departamentos),
            'Título de la iniciativa': iniciativas[i % len(iniciativas)]['titulo'],
            'Descripción': iniciativas[i % len(iniciativas)]['descripcion'],
            'Beneficios esperados': iniciativas[i % len(iniciativas)]['beneficios'],
            'Recursos necesarios': iniciativas[i % len(iniciativas)]['recursos'],
            'Tiempo estimado': iniciativas[i % len(iniciativas)]['tiempo'],
            'Presupuesto estimado': iniciativas[i % len(iniciativas)]['presupuesto']
        }
        data_rows.append(row)
    
    return pd.DataFrame(data_rows)
            'presupuesto': '$25,000'
        },
        {
            'titulo': 'Automatización de procesos de testing con ML',
            'descripcion': 'Crear suite de testing automatizado que aprenda de errores previos para mejorar cobertura',
            'beneficios': 'Reducción del 50% en tiempo de testing',
            'recursos': '1 ingeniero QA senior, herramientas de testing, 2 meses',
            'tiempo': '2 meses',
            'presupuesto': '$15,000'
        },
        {
            'titulo': 'Plataforma de capacitación con realidad virtual',
            'descripcion': 'Sistema VR para entrenamientos inmersivos que reduzcan curva de aprendizaje',
            'beneficios': 'Mejora del 40% en retención de conocimiento',
            'recursos': 'Equipos VR, desarrollador Unity, contenido 3D',
            'tiempo': '4 meses',
            'presupuesto': '$45,000'
        },
        {
            'titulo': 'Chatbot multicanal con procesamiento de lenguaje natural',
            'descripcion': 'Bot inteligente que atienda consultas en web, WhatsApp y redes sociales',
            'beneficios': 'Reducción del 60% en tiempo de respuesta',
            'recursos': 'Plataforma NLP, integrador, diseñador conversacional',
            'tiempo': '2 meses',
            'presupuesto': '$20,000'
        },
        {
            'titulo': 'Sistema blockchain para trazabilidad de productos',
            'descripcion': 'Implementar blockchain para garantizar autenticidad y trazabilidad completa',
            'beneficios': 'Eliminación del 95% de productos falsificados',
            'recursos': 'Arquitecto blockchain, 3 desarrolladores, infraestructura',
            'tiempo': '6 meses',
            'presupuesto': '$75,000'
        },
        {
            'titulo': 'App móvil de productividad con gamificación',
            'descripcion': 'Aplicación que convierta tareas en juegos para aumentar engagement',
            'beneficios': 'Incremento del 35% en productividad individual',
            'recursos': '2 desarrolladores móviles, diseñador UX/UI',
            'tiempo': '3 meses',
            'presupuesto': '$30,000'
        },
        {
            'titulo': 'Dashboard predictivo de mantenimiento con IoT',
            'descripcion': 'Sensores IoT que predigan fallas antes de que ocurran',
            'beneficios': 'Reducción del 70% en paradas no planificadas',
            'recursos': 'Sensores IoT, plataforma de análisis, técnicos',
            'tiempo': '5 meses',
            'presupuesto': '$55,000'
        },
        {
            'titulo': 'Marketplace interno de conocimiento',
            'descripcion': 'Plataforma donde empleados compartan y moneticen conocimiento interno',
            'beneficios': 'Aumento del 50% en colaboración interdepartamental',
            'recursos': 'Desarrolladores full-stack, diseñador, community manager',
            'tiempo': '4 meses',
            'presupuesto': '$35,000'
        },
        {
            'titulo': 'Sistema de reconocimiento facial para seguridad',
            'descripcion': 'Implementar acceso biométrico en todas las instalaciones',
            'beneficios': 'Mejora del 90% en control de accesos',
            'recursos': 'Cámaras especializadas, software IA, integradores',
            'tiempo': '3 meses',
            'presupuesto': '$40,000'
        },
        {
            'titulo': 'Asistente virtual de voz para reuniones',
            'descripcion': 'IA que transcriba, resuma y genere acciones de reuniones automáticamente',
            'beneficios': 'Ahorro de 5 horas semanales por empleado',
            'recursos': 'Licencias de IA, desarrollador, trainer',
            'tiempo': '2 meses',
            'presupuesto': '$18,000'
        },
        {
            'titulo': 'Plataforma de innovación abierta con clientes',
            'descripcion': 'Portal donde clientes propongan mejoras y voten ideas',
            'beneficios': 'Incremento del 40% en satisfacción del cliente',
            'recursos': 'Desarrolladores, moderadores, sistema de recompensas',
            'tiempo': '3 meses',
            'presupuesto': '$28,000'
        },
        {
            'titulo': 'Gemelo digital de planta de producción',
            'descripcion': 'Réplica virtual de toda la operación para simulaciones y optimización',
            'beneficios': 'Optimización del 25% en eficiencia operativa',
            'recursos': 'Consultores especializados, software de simulación',
            'tiempo': '8 meses',
            'presupuesto': '$120,000'
        },
        {
            'titulo': 'Sistema de firma digital con blockchain',
            'descripcion': 'Eliminar papel implementando firmas digitales verificables',
            'beneficios': 'Reducción del 100% en uso de papel para contratos',
            'recursos': 'Plataforma de firma digital, capacitación legal',
            'tiempo': '2 meses',
            'presupuesto': '$15,000'
        },
        {
            'titulo': 'Red neuronal para detección de fraudes',
            'descripcion': 'IA que detecte patrones anómalos en transacciones en tiempo real',
            'beneficios': 'Prevención del 85% de intentos de fraude',
            'recursos': 'Data scientists, infraestructura GPU, datos históricos',
            'tiempo': '5 meses',
            'presupuesto': '$65,000'
        },
        {
            'titulo': 'Aplicación AR para capacitación técnica',
            'descripcion': 'Realidad aumentada que guíe paso a paso en procedimientos complejos',
            'beneficios': 'Reducción del 60% en errores de procedimiento',
            'recursos': 'Desarrollador AR, dispositivos, contenido 3D',
            'tiempo': '4 meses',
            'presupuesto': '$42,000'
        },
        {
            'titulo': 'Bot de reclutamiento con IA',
            'descripcion': 'Automatizar screening inicial de candidatos con entrevistas por chat',
            'beneficios': 'Reducción del 70% en tiempo de reclutamiento',
            'recursos': 'Plataforma de IA conversacional, psicólogo organizacional',
            'tiempo': '2 meses',
            'presupuesto': '$22,000'
        },
        {
            'titulo': 'Sistema de recomendación de productos con ML',
            'descripcion': 'Motor que sugiera productos basado en comportamiento del usuario',
            'beneficios': 'Incremento del 45% en ventas cruzadas',
            'recursos': 'Data scientists, infraestructura cloud',
            'tiempo': '3 meses',
            'presupuesto': '$38,000'
        },
        {
            'titulo': 'Plataforma de mentoring con matching automático',
            'descripcion': 'Sistema que conecte mentores y aprendices según perfiles e intereses',
            'beneficios': 'Mejora del 30% en desarrollo profesional',
            'recursos': 'Desarrolladores, psicólogo, diseñador UX',
            'tiempo': '3 meses',
            'presupuesto': '$25,000'
        },
        {
            'titulo': 'Dashboard de sostenibilidad en tiempo real',
            'descripcion': 'Monitoreo continuo de métricas ambientales y sociales',
            'beneficios': 'Reducción del 20% en huella de carbono',
            'recursos': 'Sensores ambientales, analista de datos',
            'tiempo': '2 meses',
            'presupuesto': '$18,000'
        },
        {
            'titulo': 'Automatización RPA de procesos administrativos',
            'descripcion': 'Robots de software para tareas repetitivas administrativas',
            'beneficios': 'Liberación del 40% del tiempo en tareas manuales',
            'recursos': 'Licencias RPA, consultor de procesos',
            'tiempo': '3 meses',
            'presupuesto': '$32,000'
        },
        {
            'titulo': 'Sistema de gestión de ideas con votación',
            'descripcion': 'Plataforma colaborativa para proponer y votar mejoras internas',
            'beneficios': 'Aumento del 60% en participación en innovación',
            'recursos': 'Desarrollador full-stack, facilitador de innovación',
            'tiempo': '2 meses',
            'presupuesto': '$20,000'
        },
        {
            'titulo': 'Análisis predictivo de rotación de personal',
            'descripcion': 'Modelo ML que identifique empleados en riesgo de renuncia',
            'beneficios': 'Reducción del 30% en rotación no deseada',
            'recursos': 'Data scientist, analista de RRHH',
            'tiempo': '3 meses',
            'presupuesto': '$28,000'
        },
        {
            'titulo': 'Plataforma de economía circular interna',
            'descripcion': 'Sistema para reutilizar y compartir recursos entre departamentos',
            'beneficios': 'Ahorro del 25% en compras de materiales',
            'recursos': 'Desarrolladores, coordinador de sostenibilidad',
            'tiempo': '4 meses',
            'presupuesto': '$35,000'
        },
        {
            'titulo': 'Chatbot de onboarding para nuevos empleados',
            'descripcion': 'Asistente virtual que guíe en primeros días de trabajo',
            'beneficios': 'Reducción del 50% en tiempo de adaptación',
            'recursos': 'Desarrollador de chatbots, especialista en RRHH',
            'tiempo': '2 meses',
            'presupuesto': '$16,000'
        },
        {
            'titulo': 'Sistema de gestión visual con kanban digital',
            'descripcion': 'Tableros digitales interactivos para gestión de proyectos',
            'beneficios': 'Mejora del 35% en cumplimiento de plazos',
            'recursos': 'Licencias de software, capacitador ágil',
            'tiempo': '1 mes',
            'presupuesto': '$10,000'
        },
        {
            'titulo': 'Plataforma de crowdsourcing para innovación',
            'descripcion': 'Abrir retos de innovación a comunidad externa',
            'beneficios': 'Acceso a 10x más ideas innovadoras',
            'recursos': 'Plataforma web, community manager, premios',
            'tiempo': '3 meses',
            'presupuesto': '$30,000'
        },
        {
            'titulo': 'Sistema de análisis de sentimientos en redes',
            'descripcion': 'Monitorear percepción de marca en tiempo real',
            'beneficios': 'Respuesta 80% más rápida a crisis de reputación',
            'recursos': 'Herramientas de social listening, analista',
            'tiempo': '2 meses',
            'presupuesto': '$24,000'
        },
        {
            'titulo': 'Laboratorio de innovación móvil',
            'descripcion': 'Unidad móvil para probar innovaciones en diferentes ubicaciones',
            'beneficios': 'Validación 3x más rápida de conceptos',
            'recursos': 'Vehículo adaptado, equipamiento, facilitadores',
            'tiempo': '4 meses',
            'presupuesto': '$60,000'
        },
        {
            'titulo': 'Sistema de gestión de conocimiento con IA',
            'descripcion': 'Base de conocimiento que aprenda y sugiera información relevante',
            'beneficios': 'Reducción del 40% en tiempo de búsqueda de información',
            'recursos': 'Plataforma de IA, arquitecto de información',
            'tiempo': '3 meses',
            'presupuesto': '$35,000'
        },
        {
            'titulo': 'Red de sensores para smart building',
            'descripcion': 'Convertir oficinas en espacios inteligentes y eficientes',
            'beneficios': 'Ahorro del 30% en consumo energético',
            'recursos': 'Sensores IoT, plataforma de gestión, instaladores',
            'tiempo': '5 meses',
            'presupuesto': '$50,000'
        },
        {
            'titulo': 'Programa de intraemprendimiento digital',
            'descripcion': 'Incubadora interna para proyectos digitales de empleados',
            'beneficios': 'Generación de 5 nuevas líneas de negocio al año',
            'recursos': 'Mentores, presupuesto semilla, espacio de trabajo',
            'tiempo': '6 meses',
            'presupuesto': '$80,000'
        },
        {
            'titulo': 'Sistema de realidad mixta para diseño',
            'descripcion': 'Herramienta MR para diseño colaborativo 3D en tiempo real',
            'beneficios': 'Reducción del 50% en tiempo de prototipado',
            'recursos': 'Dispositivos HoloLens, desarrollador MR',
            'tiempo': '4 meses',
            'presupuesto': '$55,000'
        },
        {
            'titulo': 'Plataforma de microlearning con IA',
            'descripcion': 'Sistema que personalice rutas de aprendizaje según cada empleado',
            'beneficios': 'Mejora del 45% en competencias técnicas',
            'recursos': 'Plataforma LMS con IA, diseñador instruccional',
            'tiempo': '3 meses',
            'presupuesto': '$32,000'
        },
        {
            'titulo': 'Centro de comando digital integrado',
            'descripcion': 'Sala de control con visualización en tiempo real de toda la operación',
            'beneficios': 'Toma de decisiones 60% más rápida',
            'recursos': 'Pantallas, software de integración, analistas',
            'tiempo': '4 meses',
            'presupuesto': '$70,000'
        },
        {
            'titulo': 'Bot de análisis de contratos con NLP',
            'descripcion': 'IA que revise y extraiga información clave de contratos',
            'beneficios': 'Reducción del 80% en tiempo de revisión legal',
            'recursos': 'Modelo NLP especializado, abogado trainer',
            'tiempo': '3 meses',
            'presupuesto': '$40,000'
        },
        {
            'titulo': 'Sistema de pagos con criptomonedas',
            'descripcion': 'Aceptar pagos en criptomonedas principales',
            'beneficios': 'Acceso a nuevo segmento de mercado del 15%',
            'recursos': 'Integrador blockchain, asesor financiero',
            'tiempo': '2 meses',
            'presupuesto': '$25,000'
        },
        {
            'titulo': 'Plataforma de bienestar con wearables',
            'descripcion': 'App que conecte con dispositivos de salud para programa wellness',
            'beneficios': 'Reducción del 20% en costos de seguro médico',
            'recursos': 'Desarrollador de apps, dispositivos wearables',
            'tiempo': '3 meses',
            'presupuesto': '$35,000'
        },
        {
            'titulo': 'Sistema de traducción en tiempo real',
            'descripcion': 'Herramienta para reuniones multiidioma con traducción simultánea',
            'beneficios': 'Eliminación de barreras de idioma en equipos globales',
            'recursos': 'Licencias de IA de traducción, equipos de audio',
            'tiempo': '2 meses',
            'presupuesto': '$20,000'
        },
        {
            'titulo': 'Marketplace de habilidades internas',
            'descripcion': 'Plataforma para intercambiar habilidades entre empleados',
            'beneficios': 'Aumento del 40% en desarrollo de habilidades',
            'recursos': 'Desarrollador, diseñador UX, coordinador',
            'tiempo': '3 meses',
            'presupuesto': '$28,000'
        },
        {
            'titulo': 'Sistema de gestión de energía con IA',
            'descripcion': 'Optimización automática del consumo energético',
            'beneficios': 'Reducción del 35% en costos de energía',
            'recursos': 'Sensores, plataforma de IA, ingeniero energético',
            'tiempo': '4 meses',
            'presupuesto': '$45,000'
        },
        {
            'titulo': 'Laboratorio de prototipado rápido',
            'descripcion': 'Espacio con impresoras 3D y herramientas de fabricación digital',
            'beneficios': 'Reducción del 70% en tiempo de prototipado',
            'recursos': 'Equipos de fabricación, técnico especializado',
            'tiempo': '3 meses',
            'presupuesto': '$50,000'
        },
        {
            'titulo': 'Asistente de código con IA',
            'descripcion': 'Herramienta que sugiera y corrija código en tiempo real',
            'beneficios': 'Aumento del 40% en productividad de desarrollo',
            'recursos': 'Licencias de GitHub Copilot o similar',
            'tiempo': '1 mes',
            'presupuesto': '$12,000'
        },
        {
            'titulo': 'Sistema de gestión de crisis con IA',
            'descripcion': 'Plataforma que detecte y gestione crisis potenciales',
            'beneficios': 'Respuesta 5x más rápida ante emergencias',
            'recursos': 'Software de monitoreo, protocolo de crisis',
            'tiempo': '3 meses',
            'presupuesto': '$38,000'
        },
        {
            'titulo': 'Red de innovación con universidades',
            'descripcion': 'Colaboración estructurada con centros académicos',
            'beneficios': 'Acceso a talento e investigación de vanguardia',
            'recursos': 'Coordinador académico, presupuesto para proyectos',
            'tiempo': '6 meses',
            'presupuesto': '$60,000'
        },
        {
            'titulo': 'Sistema de gestión de carbono',
            'descripcion': 'Plataforma para medir y compensar huella de carbono',
            'beneficios': 'Alcanzar neutralidad de carbono en 2 años',
            'recursos': 'Software especializado, consultor ambiental',
            'tiempo': '4 meses',
            'presupuesto': '$40,000'
        },
        {
            'titulo': 'Plataforma de eventos virtuales inmersivos',
            'descripcion': 'Espacios virtuales 3D para eventos y conferencias',
            'beneficios': 'Ahorro del 60% en costos de eventos presenciales',
            'recursos': 'Plataforma de metaverso, diseñador 3D',
            'tiempo': '3 meses',
