import os
import pandas as pd
import numpy as np


class ResultsSheet:
    CYCLE_COUNTS = [9, 6, 3]
    QID_COLUMN = "ID_Questão"
    ANSWER_COLUMN = "Resposta"

    def configure(self):
        self.set_filename()
        self.set_is_mirim()
        self.set_question_count()
        self.set_correct_answers()
        self.set_minimum_to_pass()
        print("Configurações atualizadas.")

    def prepare_data(self):
        self.load_file()
        self.load_qids()
        self.validate_answers()
        self.fix_category_name()

    # ---
    # CONFIGURE
    # ---

    def set_filename(self):
        self.filename = input(
            "==> Cole aqui o nome do arquivo, localizado na mesma pasta do script: "
        )
        if not os.path.exists(self.filename):
            raise ValueError("O arquivo não existe!")

    def set_is_mirim(self):
        answer = input("==> A planilha é de resultados da Mirim? (s/N) ").strip()
        self.is_mirim = answer.lower() in ["s", "sim", "y"]
        if self.is_mirim:
            print("Considerando como categoria MIRIM")
        else:
            print("Considerando como categoria REGULAR/ABERTA")

    def set_correct_answers(self):
        print(
            f"==> Escreva o gabarito das {self.question_count} questões uma após a outra"
        )
        prompt = input("==> (ex. ABDCBDEBACD...) ").strip().lower()
        if len(prompt) != self.question_count:
            raise ValueError(f"Você deve inserir {self.question_count} gabaritos")
        for i, answer in enumerate(prompt):
            print(f"Gabarito Q{i + 1}: {answer}")
        self.answer_list = list(prompt)

    def set_minimum_to_pass(self):
        prompt = input(
            "==> Qual é o mínimo de questões para ser classificado? "
        ).strip()
        self.minimum_count = int(prompt)
        if self.minimum_count > self.question_count:
            raise ValueError(f"O mínimo não pode ser maior que {self.question_count}")
        print(f"Mínimo de questões (total): {self.minimum_count}")
        self.minimum_cycle_counts = []
        for i, maximum in enumerate(self.CYCLE_COUNTS):
            prompt = input(
                f"==> Qual é o mínimo de questões para o ciclo {i + 1}? "
            ).strip()
            minimum = int(prompt)
            if minimum > maximum:
                raise ValueError(f"O mínimo não pode ser maior que {maximum}.")
            self.minimum_cycle_counts.append(minimum)
            print(f"Mínimo de questões (ciclo {i+1}): {minimum} de {maximum}")

    def set_question_count(self):
        self.question_count = sum(self.CYCLE_COUNTS)
        print(f"Total de questões: {self.question_count}")

    # ---
    # DATA
    # ---

    def load_file(self):
        print("Carregando o arquivo...")
        if self.filename.endswith("xlsx"):
            self.df = pd.read_excel(self.filename)
        else:
            self.df = pd.read_csv(self.filename)
        print("Arquivo carregado!")

    def load_qids(self):
        self.sorted_qid_list = list(np.sort(self.df[self.QID_COLUMN].unique()))

    def validate_answers(self):
        for i, qid in enumerate(self.sorted_qid_list):
            array = self.df.loc[self.df[self.QID_COLUMN] == qid][
                self.ANSWER_COLUMN
            ].to_numpy()
            answer = self.answer_list[i]
            needs_fix = False
            if array[0] != answer:
                print(
                    f"O gabarito da Q{i + 1} (id {qid}) está como '{array[0]}' na planilha, "
                    f"e não '{answer}' como foi inserido no script"
                )
                needs_fix = True
            if not (array == answer).all():
                print(
                    f"O gabarito da Q{i + 1} (id {qid}) possui valores inconsistentes na planilha"
                )
                needs_fix = True
            if needs_fix:
                prompt = input(f"==> Deseja ajustar na planilha colocando gabarito da Q{i+1} como '{answer}'? (s/N) ").strip().lower()
                if prompt in ("s", "sim", "y"):
                    self.df.loc[self.df[self.QID_COLUMN] == qid, self.ANSWER_COLUMN] = answer
                    print("Ajustado!")
                else:
                    print("Saindo...")
                    exit(1)

    def fix_category_name(self):
        if self.is_mirim:
            self.df["Categoria"] = "Mirim"


def main():
    rs = ResultsSheet()
    rs.configure()
    rs.prepare_data()
    pass


if __name__ == "__main__":
    main()
