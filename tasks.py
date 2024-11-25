from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """

    browser.configure(
        slowmo=500,
    )

    orders = get_orders()
    open_robot_order_website()

    for order in orders:
        close_annoying_modal()
        fill_the_form(order)

        order_number = order["Order number"]
        pdf_file = store_receipt_as_pdf(order_number)
        screenshot = screenshot_robot(order_number)
        embed_screenshot_to_receipt(screenshot, pdf_file)
        browser.page().reload()

    archive_receipts()


def get_orders():
    http = HTTP()
    response = http.download("https://robotsparebinindustries.com/orders.csv", target_file="output/orders.csv", overwrite=True)

    tables = Tables()

    return tables.read_table_from_csv("output/orders.csv")


def close_annoying_modal():
    page = browser.page()

    page.click("text=OK")
   

def open_robot_order_website():
    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_html_table(page) -> str:
    locator = page.locator("table#model-info")
    locator.wait_for()
    return locator.evaluate("(e) => e.outerHTML")


def fill_the_form(order):
    head = order["Head"]
    body = order["Body"]
    legs = order["Legs"]
    address = order["Address"]

    page = browser.page()

    page.select_option("#head", value=head)
    page.click(f"#id-body-{body}")
    page.fill('input[placeholder="Enter the part number for the legs"]', legs)
    page.fill('input[placeholder="Shipping address"]', address)

    page.click("#order")

    error = page.query_selector(".alert.alert-danger")

    while error is not None:
        page.click("#order")
        error = page.query_selector(".alert.alert-danger")


def store_receipt_as_pdf(order_number):
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    path = f"output/receipt_{order_number}.pdf"

    pdf = PDF()
    pdf.html_to_pdf(receipt_html, path)

    return path


def screenshot_robot(order_number):
    page = browser.page()

    path = f"output/screenshot_{order_number}.png"

    page.locator("#robot-preview-image").screenshot(path=path, type="png")

    return path


def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()

    pdf.add_files_to_pdf(
        files=[pdf_file, screenshot],
        target_document=pdf_file
    )


def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip("./output", "receipts.zip", include="*.pdf")