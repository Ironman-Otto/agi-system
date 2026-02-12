class ConsoleDebugSink:
    def emit(self, entry):
        print("DEBUG SINK payload:", entry.payload)
