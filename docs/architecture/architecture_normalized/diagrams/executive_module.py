class ExecutiveProgram:
    def __init__(self):
        # Instantiate cognition system
        self.cognition = Cognition()  
        
        # State monitors
        self.attention_pool = 100  # Cognitive resource budget (0-100)
        self.threat_level = 0       # For fight-or-flight responses
        
    def route_input(self, input_source, input_data):
        """Decides processing path for incoming data"""
        # 1. Threat detection (subconscious always gets first dibs)
        if self._is_threatening(input_data):
            return self._emergency_process(input_data)
            
        # 2. Route by input source
        match input_source:
            case "sensor":
                return self._handle_sensor(input_data)
            case "NLP":
                return self._handle_nlp(input_data)
            case "internal":
                return self._handle_internal(input_data)
                
    def _is_threatening(self, data):
        """Subconscious threat filter (amygdala-like function)"""
        threat_signals = ["pain", "sudden_movement", "loud_sound"]
        if any(signal in data for signal in threat_signals):
            self.threat_level = 100
            return True
        return False