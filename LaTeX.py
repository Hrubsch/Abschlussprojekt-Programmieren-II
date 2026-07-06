from pylatex import (
    Document,
    Section,
    Subsection,
    Figure,
    Tabular,
    NoEscape,
    Command
)
from pylatex.utils import bold
import os


def create_latex_report(results, filename="Auswertung", title="Auswertung der Fahrraddaten"):
    doc = Document(documentclass="article")

    # Pakete
    doc.packages.append(Command("usepackage", "float"))
    doc.packages.append(Command("usepackage", "graphicx"))
    doc.packages.append(Command("usepackage", "booktabs"))
    doc.packages.append(Command("usepackage", "geometry"))
    doc.packages.append(Command("geometry", "margin=2.5cm"))

    # Titelseite
    doc.preamble.append(Command("title", title))
    doc.preamble.append(Command("author", ""))
    doc.preamble.append(Command("date", NoEscape(r"\today")))

    doc.append(NoEscape(r"\maketitle"))

    with doc.create(Section("Berechnete Kennwerte")):
        with doc.create(Tabular("lr")) as table:
            table.add_hline()
            table.add_row((bold("Kennwert"), bold("Wert")))
            table.add_hline()
            table.add_row(("Gesamtstrecke",
                           f"{results['Gesamtstrecke']:.1f} m"))
            table.add_row(("Durchschnittsgeschwindigkeit",
                           f"{results['Durchschnittsgeschwindigkeit']:.2f} m/s"))
            table.add_row(("Maximalleistung",
                           f"{results['P_max']:.1f} W"))
            table.add_row(("Gesamtzeit",
                           str(results["Gesamtzeit"])))
            table.add_row(("Gesamter Anstieg",
                           f"{results['Anstieg']:.1f} m"))
            table.add_row(("Gesamter Abstieg",
                           f"{results['Abstieg']:.1f} m"))

            table.add_hline()

    with doc.create(Section("Diagramme")):
        png_files = sorted(
            f for f in os.listdir(".")
            if f.endswith(".png")
        )
        for image in png_files:
            plotname = os.path.splitext(image)[0]
            with doc.create(Subsection(plotname)):
                with doc.create(Figure(position="H")) as fig:
                    fig.add_image(image, width=NoEscape(r"0.95\textwidth"))
                    fig.add_caption(plotname)

    doc.generate_pdf(filename,
                     clean_tex=False,
                     clean=True)

    print(f"Bericht '{filename}.pdf' wurde erstellt.")