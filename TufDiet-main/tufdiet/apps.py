from django.apps import AppConfig


class TufdietConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tufdiet'
    
    def ready(self):
        import tufdiet.signals