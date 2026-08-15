with open('d:/mvp2026/project_root/apps/procurement/models.py', 'a', encoding='utf-8') as f:
    f.write('''
class ProcurementAuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    actor_role = models.CharField(max_length=50)
    action = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=100)
    entity_id = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=50)
    safe_metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.action} on {self.entity_type} {self.entity_id} by {self.actor}"
''')
