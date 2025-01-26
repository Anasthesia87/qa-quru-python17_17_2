import requests
from allure_commons._allure import step
from allure_commons.types import AttachmentType
from selene import browser
from selene.support.conditions import have
import allure
import logging


def post_with_logging(url, **kwars):
    with allure.step("Логирование API"):
        response = requests.post(url, **kwars)
        allure.attach(body=response.text, name="Response",
                      attachment_type=AttachmentType.TEXT, extension=".txt")
        allure.attach(body=str(response.cookies), name="Cookies", attachment_type=AttachmentType.TEXT, extension=".txt")
        logging.info(f'POST: {response.request.url}')
        logging.info(f'With payload {response.request.body}')
        logging.info(f'Finished with status code {response.status_code}')
        return response


@allure.title("Добавление товара в корзину неавторизованным пользователем")
def test_add_product_though_api_unauthorized_user():
    with step("Добавление товара в пустую корзину через API"):
        response = post_with_logging("https://demowebshop.tricentis.com/addproducttocart/catalog/31/1/1")
        cookie = response.cookies.get("Nop.customer")
        allure.attach(str(response.text), 'Response text', attachment_type=AttachmentType.TEXT)

    with step("Проверка статус-кода"):
        assert response.status_code == 200
        allure.attach(f'Response status code: {response.status_code}', 'Status Code',
                      attachment_type=AttachmentType.TEXT)

    with step("Проверка добавления товара в корзину через UI"):
        browser.open('https://demowebshop.tricentis.com/')
        browser.driver.add_cookie({"name": "Nop.customer", "value": cookie})
        browser.open('https://demowebshop.tricentis.com/cart')
        browser.element('.product-name').should(have.exact_text('14.1-inch Laptop'))

    with allure.step('Очистка корзины'):
        browser.element('.qty-input').set_value('0').press_enter()


@allure.title("Добавление товара в корзину авторизованным пользователем")
def test_add_product_through_api_authorized_user():
    with step("Авторизация на сайте через API"):
        response = post_with_logging(
            "https://demowebshop.tricentis.com/login",
            data={
                "Email": "Anasthesia87@test.ru",
                "Password": "123456",
                "RememberMe": False
            },
            allow_redirects=False
        )
        cookie = response.cookies.get("NOPCOMMERCE.AUTH")

    with step("Проверка статус-кода после авторизации"):
        assert response.status_code == 302

    with step("Добавление товара в корзину через API"):
        response = post_with_logging(
            "https://demowebshop.tricentis.com/addproducttocart/catalog/31/1/1",
            cookies={"NOPCOMMERCE.AUTH": cookie}
        )

    with step("Проверка статус-кода после добавления товара"):
        assert response.status_code == 200

    with step("Переход в корзину через UI с авторизационным cookie"):
        browser.open('https://demowebshop.tricentis.com/')
        browser.driver.add_cookie({"name": "NOPCOMMERCE.AUTH", "value": cookie})
        browser.open('https://demowebshop.tricentis.com/cart')

    with step("Проверка наличия авторизации"):
        browser.element('.account').should(have.exact_text('Anasthesia87@test.ru'))

    with step("Проверка добавления товара в корзину через UI"):
        browser.element('.product-name').should(have.exact_text('14.1-inch Laptop'))

    with allure.step('Очистка корзины'):
        browser.element('.qty-input').set_value('0').press_enter()
