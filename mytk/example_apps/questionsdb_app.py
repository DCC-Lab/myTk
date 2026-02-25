from mytk import *
from dcclab import database

class QuestionDBApp(App):
    def __init__(self):
        App.__init__(self, name="Questions DB Application")
        self.window.widget.title("Questions DB")
        self.window.column_resize_weight(0, 1)
        self.questions_table = TableView(columns_labels={"qid":"qid","cours":"Cours","titre":"Titre","question":"Question", "reponse":"Reponse"})
        self.questions_table.grid_into(self.window, row=0, column=0, sticky="nswe")

        


if __name__ == "__main__":
    app = QuestionDBApp()

    app.mainloop()
