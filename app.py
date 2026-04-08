from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import os
import sys
from datetime import datetime
import json
import traceback
from pathlib import Path
import shutil

# Import the KPI Analysis class
from dashboard2 import EmployeeKPIAnalysis

# =====================================================================
# FLASK APP CONFIGURATION
# =====================================================================

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
OUTPUT_FOLDER = 'outputs'
CHARTS_FOLDER = 'static/charts'

# Flask configuration
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['SESSION_TYPE'] = 'filesystem'

# Create necessary directories
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, CHARTS_FOLDER]:
    Path(folder).mkdir(exist_ok=True)


# =====================================================================
# UTILITY FUNCTIONS
# =====================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_old_files(folder, max_age_hours=24):
    """Clean up old files to save disk space"""
    import time
    now = time.time()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            if os.stat(filepath).st_mtime < now - max_age_hours * 3600:
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")


# =====================================================================
# ROUTES - MAIN PAGES
# =====================================================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file upload and KPI generation"""
    if request.method == 'POST':
        try:
            # Check if file is in request
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400
            
            file = request.files['file']
            
            # Check if file is selected
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            # Validate file
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': 'Only CSV files are allowed'}), 400
            
            # Save file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Generate KPIs
            analyzer = EmployeeKPIAnalysis(filepath)
            kpi_df = analyzer.generate_all_kpis()
            
            # Create session-specific chart folder
            session_charts_folder = os.path.join(CHARTS_FOLDER, timestamp)
            Path(session_charts_folder).mkdir(parents=True, exist_ok=True)
            
            # Generate visualizations
            analyzer.create_visualizations(session_charts_folder)
            
            # Export reports
            excel_file = os.path.join(OUTPUT_FOLDER, f'KPI_Report_{timestamp}.xlsx')
            csv_file = os.path.join(OUTPUT_FOLDER, f'KPI_Data_{timestamp}.csv')
            
            analyzer.export_kpi_report(excel_file)
            analyzer.export_csv(csv_file)
            
            # Get summary statistics
            summary = analyzer.get_summary_statistics()
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'KPI analysis completed successfully',
                'timestamp': timestamp,
                'filename': filename,
                'summary': summary,
                'excel_file': os.path.basename(excel_file),
                'csv_file': os.path.basename(csv_file),
                'charts_folder': session_charts_folder
            }
            
            return jsonify(response_data), 200
        
        except RequestEntityTooLarge:
            return jsonify({'success': False, 'error': 'File too large (max 50MB)'}), 413
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': f'Error processing file: {str(e)}'}), 500
    
    return render_template('upload.html')


@app.route('/results/<timestamp>')
def results(timestamp):
    """Display KPI results"""
    try:
        # Reconstruct file paths
        charts_folder = os.path.join(CHARTS_FOLDER, timestamp)
        
        if not os.path.exists(charts_folder):
            flash('Results not found or session expired', 'error')
            return redirect(url_for('index'))
        
        # Get chart files
        chart_files = []
        if os.path.exists(charts_folder):
            chart_files = [f for f in os.listdir(charts_folder) if f.endswith('.png')]
        
        return render_template('results.html', 
                             timestamp=timestamp,
                             chart_files=chart_files,
                             charts_folder=f'charts/{timestamp}')
    
    except Exception as e:
        flash(f'Error loading results: {str(e)}', 'error')
        return redirect(url_for('index'))


# =====================================================================
# ROUTES - API ENDPOINTS
# =====================================================================

@app.route('/api/summary/<timestamp>')
def api_summary(timestamp):
    """API endpoint to get summary statistics"""
    try:
        # Note: You may need to reload the data or store it in session
        # For now, this is a placeholder that would need session management
        return jsonify({'success': False, 'error': 'Session data not available'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/career-cluster/<timestamp>')
def api_career_cluster(timestamp):
    """API endpoint for career cluster data"""
    try:
        return jsonify({'success': False, 'error': 'Session data not available'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================================
# ROUTES - FILE DOWNLOADS
# =====================================================================

@app.route('/download/<file_type>/<timestamp>')
def download_file(file_type, timestamp):
    """Download KPI reports"""
    try:
        if file_type == 'excel':
            filename = f'KPI_Report_{timestamp}.xlsx'
        elif file_type == 'csv':
            filename = f'KPI_Data_{timestamp}.csv'
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
        
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/download/chart/<timestamp>/<filename>')
def download_chart(timestamp, filename):
    """Download individual charts"""
    try:
        filepath = os.path.join(CHARTS_FOLDER, timestamp, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =====================================================================
# ROUTES - DOCUMENTATION & HELP
# =====================================================================

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')


@app.route('/documentation')
def documentation():
    """Documentation page"""
    return render_template('documentation.html')


# =====================================================================
# ERROR HANDLERS
# =====================================================================

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', 
                         error_code=404,
                         error_message='Page not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('error.html',
                         error_code=500,
                         error_message='Internal server error'), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return render_template('error.html',
                         error_code=413,
                         error_message='File too large (max 50MB)'), 413


# =====================================================================
# CONTEXT PROCESSORS
# =====================================================================

@app.context_processor
def inject_config():
    """Inject configuration into templates"""
    return {
        'app_name': 'Employee KPI Dashboard',
        'app_version': '1.0.0',
        'current_year': datetime.now().year
    }


# =====================================================================
# BEFORE REQUEST
# =====================================================================

@app.before_request
def cleanup_old_files():
    """Cleanup old files periodically"""
    # Run cleanup every 100 requests (not on every request for performance)
    if not hasattr(app, 'request_count'):
        app.request_count = 0
    
    app.request_count += 1
    if app.request_count % 100 == 0:
        clean_old_files(UPLOAD_FOLDER)
        clean_old_files(OUTPUT_FOLDER)


# =====================================================================
# MAIN EXECUTION
# =====================================================================

if __name__ == '__main__':
    # Development server
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )