from flask import Flask, render_template, request, jsonify
import json
import random

app = Flask(__name__)

def load_components():
    """Carga los componentes desde el archivo builds.json"""
    try:
        with open('builds.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"components": {}}

def filter_by_budget(components, budget, component_type):
    """Filtra componentes por presupuesto"""
    return [comp for comp in components if comp['price'] <= budget]

def select_component(components, budget, use_type, preferred_brands=None):
    """Selecciona el mejor componente basado en criterios"""
    if not components:
        return None
    
    # Filtrar por presupuesto
    affordable = filter_by_budget(components, budget, None)
    if not affordable:
        return None
    
    # Filtrar por marca preferida si se especifica
    if preferred_brands:
        brand_filtered = [comp for comp in affordable if any(brand.lower() in comp['name'].lower() for brand in preferred_brands)]
        if brand_filtered:
            affordable = brand_filtered
    
    # Seleccionar componente optimizado por tipo de uso
    if use_type == 'gaming':
        # Para gaming, priorizar rendimiento
        return max(affordable, key=lambda x: x['price'])
    elif use_type == 'design':
        # Para diseño, balance entre rendimiento y estabilidad
        return max(affordable, key=lambda x: x['price'])
    elif use_type == 'office':
        # Para oficina, priorizar valor por dinero
        return min(affordable, key=lambda x: x['price'])
    else:
        # Por defecto, seleccionar algo intermedio
        return affordable[len(affordable) // 2] if affordable else None

def build_pc(budget, use_type, preferred_brands=None):
    """Construye una PC completa basada en los parámetros"""
    components_data = load_components()
    components = components_data.get('components', {})
    
    # Distribución de presupuesto por componente
    budget_distribution = {
        'gaming': {
            'gpu': 0.35,
            'cpu': 0.25,
            'ram': 0.15,
            'storage': 0.10,
            'motherboard': 0.10,
            'psu': 0.05
        },
        'design': {
            'gpu': 0.30,
            'cpu': 0.30,
            'ram': 0.20,
            'storage': 0.10,
            'motherboard': 0.07,
            'psu': 0.03
        },
        'office': {
            'gpu': 0.15,
            'cpu': 0.25,
            'ram': 0.20,
            'storage': 0.15,
            'motherboard': 0.15,
            'psu': 0.10
        }
    }
    
    distribution = budget_distribution.get(use_type, budget_distribution['office'])
    selected_components = {}
    total_cost = 0
    
    # Seleccionar componentes
    for component_type, percentage in distribution.items():
        component_budget = budget * percentage
        available_components = components.get(component_type, [])
        
        selected = select_component(available_components, component_budget, use_type, preferred_brands)
        if selected:
            selected_components[component_type] = selected
            total_cost += selected['price']
    
    return {
        'components': selected_components,
        'total_cost': total_cost,
        'budget_used': (total_cost / budget) * 100 if budget > 0 else 0,
        'use_type': use_type,
        'success': len(selected_components) > 0
    }

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/build', methods=['POST'])
def generate_build():
    """API endpoint para generar build de PC"""
    try:
        data = request.get_json()
        
        # Validar datos de entrada
        budget = float(data.get('budget', 0))
        use_type = data.get('use_type', 'office').lower()
        preferred_brands = data.get('preferred_brands', [])
        
        if budget <= 0:
            return jsonify({
                'success': False,
                'error': 'El presupuesto debe ser mayor a 0'
            }), 400
        
        # Generar build
        build_result = build_pc(budget, use_type, preferred_brands)
        
        return jsonify(build_result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/health')
def health_check():
    """Endpoint de salud para verificar que la API funciona"""
    return jsonify({'status': 'OK', 'message': 'CreateYouPC API funcionando correctamente'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)