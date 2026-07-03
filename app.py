from flask import Flask, jsonify, render_template
from config import Config
from routes.main import main_bp
from routes.api import api_bp

def create_app():
    """
    Flask Application Factory.
    Initializes configuration, directories, registers blueprints, and error handlers.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        # Determine if requesting API or web page
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "Endpoint not found (404)"}), 404
        return render_template('base.html', title="404 - Not Found", error_message="The page you are looking for does not exist."), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import request
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": f"Internal Server Error: {str(e)}"}), 500
        return render_template('base.html', title="500 - Server Error", error_message="An internal server error occurred. Please check logs."), 500
        
    return app

if __name__ == '__main__':
    app = create_app()
    print("AI News Reel Studio has started!")
    print(f"Base Directory: {Config.BASE_DIR}")
    print("Navigate to http://localhost:5000 in your browser.")
    app.run(host='0.0.0.0', port=5000, debug=True)
