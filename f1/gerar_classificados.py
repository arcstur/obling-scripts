import os
import pandas as pd
import numpy as np


class ResultsSheet:
    CYCLE_COUNTS = [9, 6, 3]
    QID_COLUMN = "ID_Questão"
    FID_COLUMN = "Fractal ID"
    Q_SELECTED_COLUMN = "Selecionado"
    Q_ANSWER_COLUMN = "Resposta"
    ANSWER_COLUMN = "Resposta"
    AGGREGATE_COLUMNS = [
        "Categoria",
        "Nome",
        "Email",
        "Data de inscrição",
        "Sexo",
        "UF(Origem)",
        "Cidade(Origem)",
        "Código INEP",
        "Escola",
        "UF",
        "Cidade",
        "Série",
    ]
    CORRECT_COUNT_COLUMN = "Acertos"
    CLASSIFIED_COLUMN = "Classificado"
    GRADE_COLUMN = "Nota"

    def configure(self):
        self._set_filename()
        self._set_is_mirim()
        self._set_question_count()
        self._set_correct_answers()
        self._set_minimum_to_pass()
        print("Configurações atualizadas.")

    def prepare_data(self):
        self._load_file()
        self._load_qids()
        self._validate_answers()
        self._fix_category_name()

    def process_data(self):
        self._count_correct_answers()
        self._count_correct_answers_per_cycle()
        self._prepare_results()
        self._evaluate_results()

    def finalize(self):
        self._print_counts()
        self._export()
        self._export_to_system()

    # ---
    # CONFIGURE
    # ---

    def _set_filename(self):
        self.filename = input(
            "==> Cole aqui o nome do arquivo ('.._resultados.xlsx'), localizado na mesma pasta do script: "
        )
        if not os.path.exists(self.filename):
            raise ValueError("O arquivo não existe!")

    def _set_is_mirim(self):
        answer = input("==> A planilha é de resultados da Mirim? (s/N) ").strip()
        self.is_mirim = answer.lower() in ["s", "sim", "y"]
        if self.is_mirim:
            print("Considerando como categoria MIRIM")
        else:
            print("Considerando como categoria REGULAR/ABERTA")

    def _set_correct_answers(self):
        print(
            f"==> Escreva o gabarito das {self.question_count} questões uma após a outra"
        )
        prompt = input("==> (ex. ABDCBDEBACD...) ").strip().lower()
        if len(prompt) != self.question_count:
            raise ValueError(f"Você deve inserir {self.question_count} gabaritos")
        for i, answer in enumerate(prompt):
            print(f"Gabarito Q{i + 1}: {answer}")
        self.answer_list = list(prompt)

    def _set_minimum_to_pass(self):
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
            print(f"Mínimo de questões (ciclo {i + 1}): {minimum} de {maximum}")

    def _set_question_count(self):
        self.question_count = sum(self.CYCLE_COUNTS)
        print(f"Total de questões: {self.question_count}")

    # ---
    # DATA
    # ---

    def _load_file(self):
        print("Carregando o arquivo...")
        if self.filename.endswith("xlsx"):
            self.df = pd.read_excel(self.filename, engine="calamine")
        else:
            self.df = pd.read_csv(self.filename)
        print("Arquivo carregado!")

    def _load_qids(self):
        self.sorted_qid_list = list(np.sort(self.df[self.QID_COLUMN].unique()))

    def _validate_answers(self):
        print("Validando respostas...")
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
            if not (array == array[0]).all():
                print(
                    f"O gabarito da Q{i + 1} (id {qid}) possui valores inconsistentes na planilha"
                )
                needs_fix = True
            if needs_fix:
                prompt = (
                    input(
                        f"==> Deseja ajustar na planilha colocando gabarito da Q{i + 1} como '{answer}'? (s/N) "
                    )
                    .strip()
                    .lower()
                )
                if prompt in ("s", "sim", "y"):
                    self.df.loc[self.df[self.QID_COLUMN] == qid, self.ANSWER_COLUMN] = (
                        answer
                    )
                    print("Ajustado!")
                else:
                    print("Saindo...")
                    exit(1)

    def _fix_category_name(self):
        if self.is_mirim:
            self.df["Categoria"] = "Mirim"

    # ---
    # COUNTING
    # ---

    def _count_correct_answers(self):
        print("Contando acertos totais por participante...")
        self.df[self.CORRECT_COUNT_COLUMN] = (
            self.df["Selecionado"] == self.df["Resposta"]
        )

    def _cycles_qid_lists(self):
        qid_lists = []
        current_count = 0
        for i, cycle_count in enumerate(self.CYCLE_COUNTS):
            qid_lists.append(
                self.sorted_qid_list[current_count : current_count + cycle_count]
            )
            current_count = cycle_count
        return qid_lists

    def _count_correct_answers_per_cycle(self):
        print("Contando acertos por ciclo por participante...")
        self.df[self.CORRECT_COUNT_COLUMN] = (
            self.df["Selecionado"] == self.df["Resposta"]
        )
        for i, cycle_qid_list in enumerate(self._cycles_qid_lists()):
            name = f"C{i + 1}"
            self.df[name] = (
                self.df[self.QID_COLUMN].apply(lambda x: x in cycle_qid_list)
                & self.df[self.CORRECT_COUNT_COLUMN]
            )

    def _prepare_results(self):
        print("Agregando resultados...")
        agg_dict = (
            {column: "first" for column in self.AGGREGATE_COLUMNS}
            | {
                self.CORRECT_COUNT_COLUMN: "sum",
            }
            | {f"C{i + 1}": "sum" for i in range(len(self.CYCLE_COUNTS))}
        )
        self.df_results = (
            self.df.groupby(self.FID_COLUMN)
            .agg(agg_dict)
            .sort_values(by=[self.CORRECT_COUNT_COLUMN], ascending=False)
        )

    def _evaluate_results(self):
        print("Classificando participantes...")
        self.df_results[self.CLASSIFIED_COLUMN] = (
            self.df_results[self.CORRECT_COUNT_COLUMN] >= self.minimum_count
        )
        for i, min_count in enumerate(self.minimum_cycle_counts):
            name = f"C{i + 1}"
            self.df_results[self.CLASSIFIED_COLUMN] &= (
                self.df_results[name] >= min_count
            )

    # ---
    # PRINTING
    # ---

    def _print_counts(self):
        print(
            self.df_results.groupby("Categoria")[self.CLASSIFIED_COLUMN]
            .value_counts()
            .sort_index()
        )

    def _export(self):
        cat = "Mirim" if self.is_mirim else "RegularAberta"
        fn = f"../Classificados-{cat}.xlsx"
        print(f"Exportando para '{fn}'...")
        self.df_results.to_excel(fn)

    def _export_to_system(self):
        cat = "Mirim" if self.is_mirim else "RegularAberta"
        fn = f"../NotasSistema-{cat}.csv"
        print(f"Exportando para '{fn}'...")
        self.df_results[self.GRADE_COLUMN] = 1 * self.df_results[self.CLASSIFIED_COLUMN]
        self.df_results[[self.GRADE_COLUMN]].to_csv(fn)


def main():
    rs = ResultsSheet()
    rs.configure()
    rs.prepare_data()
    rs.process_data()
    rs.finalize()
    pass


if __name__ == "__main__":
    main()
