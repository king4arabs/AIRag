class ConfigManager:
    def __init__(self):
        self.llm_provider = 'default_provider'
        self.vector_store_path = './vector_store'
        self.doc_processing_params = {
            'max_tokens': 1000,
            'temperature': 0.7,
        }
        self.compliance_standards = ['GDPR', 'CCPA']

    def set_llm_provider(self, provider):
        self.llm_provider = provider

    def set_vector_store_path(self, path):
        self.vector_store_path = path

    def update_doc_processing_params(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.doc_processing_params:
                self.doc_processing_params[key] = value

    def set_compliance_standards(self, standards):
        self.compliance_standards = standards

    def get_config(self):
        return {
            'llm_provider': self.llm_provider,
            'vector_store_path': self.vector_store_path,
            'doc_processing_params': self.doc_processing_params,
            'compliance_standards': self.compliance_standards,
        }