import threading


class TMImportThread(threading.Thread):
    def __init__(self, entries, TMEntryModel, translation_memory, relevant_tm_entries, **kwargs):
        self.entries = entries
        self.relevant_tm_entries = relevant_tm_entries
        self.TMEntryModel = TMEntryModel
        self.translation_memory = translation_memory
        super(TMImportThread, self).__init__(**kwargs)

    def run(self):
        for entry in self.entries:
            tm_entries = self.relevant_tm_entries.filter(source = entry[1])
            if len(tm_entries) == 1:
                tm_entry = tm_entries[0]
            else:
                tm_entry = self.TMEntryModel()
                tm_entry.source = entry[1]
                tm_entry.translationmemory = self.translation_memory

            tm_entry.target = entry[2]
            tm_entry.save()
