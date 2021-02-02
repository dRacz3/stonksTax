from parsers import parse_revolut_invoice

from processing.modifiers import calculate_szja_for_2020

paths = [f'D:\Trading/{i}.pdf' for i in range(6, 13)]
activity = [parse_revolut_invoice(path) for path in paths]
szja = calculate_szja_for_2020(activity)

print(f"You will have to pay the total of {szja} HUF as SZJA for 2020")