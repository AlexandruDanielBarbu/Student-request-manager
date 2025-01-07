from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_pdf(filename, student_first_name, student_last_name, student_addr, student_group, student_id,
                 subject_list, old_subject, new_subject, new_teacher):

    if old_subject in subject_list:
        c = canvas.Canvas(filename, pagesize=letter)

        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(306, 750, "Cerere schimbare de materie")

        c.setFont("Helvetica", 12)
        c.drawString(
            75, 680,
            f"      Subsemnatul {student_first_name} {student_last_name}, student la Facultatea Automatica si Calculatoare,"
        )

        c.drawString(
            75, 660,
            f"grupa {student_group}, cu domiciliu {student_addr}, rog schimbarea materiei {old_subject}, cu materia"
        )

        c.drawString(
            75, 640,
            f"{new_subject}, coordonata de profesor {new_teacher}."
        )

        date = datetime.now().strftime("%d.%m.%Y")
        c.drawString(
            75, 150,
            f"Data: {date}"
        )

        c.drawString(
            400, 150, "Semnatura:"
        )

        try:
            img = "semnaturi/semnatura" + str(student_id) + ".jpg"
            c.drawImage(img, 400, 40, width=100, height=100)
        except Exception as e:
            c.drawString(
                400, 40, "[Image not found: Replace with your image path]")

        c.save()
        print(f"PDF generated: {filename}")
    else:
        print("Studentul nu are aceasta materie in foaia matricola")


def main():
    student_first_name = input()
    student_last_name = input()
    student_addr = input()
    student_group = input()
    try:
        student_id = int(input())
    except TypeError:
        pass
    subject_list = input().split(" ")
    old_subject = input()
    new_subject = input()
    new_teacher = input()
    generate_pdf("Cerere schimbare materie.pdf", student_first_name, student_last_name, student_addr, student_group, student_id,
                 subject_list, old_subject, new_subject, new_teacher)


if __name__ == "__main__":
    main()
