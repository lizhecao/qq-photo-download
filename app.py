# -*- coding: utf-8 -*-
import os
import time
import unittest

from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

import conf


class UntitledTestCase(unittest.TestCase):
    def setUp(self):
        # 图片存储路径
        self.store_dir = r"/Users/lizhecao/python/qq-photo-download/imgs"

        options = webdriver.ChromeOptions()
        # 设置图片存储位置，不弹出下载通知框
        options.add_experimental_option("prefs", {
            "download.default_directory": self.store_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
        })
        # 显示chrome浏览器，没显示不知为啥老是没下载。。
        options.headless = False

        # chromedriver 存储路径，我是放在跟py文件同个目录下
        self.driver = webdriver.Chrome(executable_path='./chromedriver', chrome_options=options)

        self.driver.maximize_window()
        self.driver.implicitly_wait(10)
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_untitled_test_case(self):
        driver = self.driver
        driver.get("http://i.qq.com/")
        time.sleep(2)
        # 登录表单在页面的框架中，所以要切换到该框架               重点
        driver.switch_to.frame('login_frame')

        # 填写用户名密码
        driver.find_element_by_id("switcher_plogin").click()
        name = driver.find_element_by_id("u")
        name.send_keys(conf.name)
        passwd = driver.find_element_by_id("p")
        passwd.send_keys(conf.passwd)

        driver.find_element_by_id("login_button").click()

        time.sleep(2)

        self.enter_photograph_page(driver)

        # 遍历所有的相册
        photographs = driver.find_elements_by_xpath("//*[contains(@class, 'js-album-list-ul')]/li")
        print '相册数量: {0}'.format(len(photographs))
        for photograph_number in range(12, len(photographs)):
            photograph = driver.find_element_by_xpath("//*[contains(@class, 'js-album-list-ul')]/li[{0}]"
                                                       .format(photograph_number + 1))
            # 获取相册名称
            photograph_name = photograph.find_element_by_tag_name("div").get_attribute("data-name")
            print u'相册名称: {0}'.format(photograph_name)

            # 创建相册存储目录
            real_dir = self.store_dir + "/" + photograph_name
            try:
                os.mkdir(real_dir)
            except:
                pass
            # 打开相册 （用ActionChains 可以防止相册不在页面中 报not ClickAble异常
            photograph_a = photograph.find_element_by_tag_name("a")
            ActionChains(driver).move_to_element(photograph_a).pause(2).click(photograph_a).perform()
            # photograph.find_element_by_tag_name("a").click()

            time.sleep(2)

            # 查下总共有多少张图片
            photo_total_str = driver.find_element_by_class_name("j-pl-albuminfo-total").text
            photo_total = int(photo_total_str[:-1])
            print "该相册图片数量: {0}".format(photo_total)

            # 点击相册的第一个图片
            # 这里为啥用ActionChains 因为第一个相册有点出屏幕了，所以click会报 not ClickAble异常
            # 所以用actionChains先move到这个图片再点击就稳了
            first_photo = driver.find_element_by_xpath("//a[contains(@class, 'j-pl-photoitem-imgctn')]")
            ActionChains(driver).move_to_element(first_photo).click(first_photo).perform()
            # driver.find_element_by_xpath("//a[contains(@class, 'j-pl-photoitem-imgctn')]").click()

            driver.switch_to.parent_frame()

            time.sleep(2)
            # 开始循环翻页下载图片
            for x in range(photo_total):
                print '移动到other菜单并点击下载'
                # 使用ActionChains 来实现这种关联操作
                othermenu_btn = driver.find_element_by_id("js-othermenu-btn")
                downloadPhoto_btn = driver.find_element_by_id("js-btn-downloadPhoto")
                ActionChains(driver).move_to_element(othermenu_btn).click(downloadPhoto_btn).perform()

                """
                文件重命名，默认是default.jpeg文件
                为什么要重命名? 因为虽然默认情况下浏览器下载的文件会自动重命名为 default(x).jpeg，
                但是不知道为啥，在default(100).jpeg 之后就会弹出通知框，并且选择下载之后会提示是否
                覆盖default.jpeg文件，也就是说不能重命名default(101).jpeg或者以上的了。。。
                """
                while True:
                    try:
                        os.rename(u"%s/default.jpeg" % self.store_dir, u"%s/%d.jpeg" % (real_dir, x))
                        print 'rename default.jpeg'
                        break
                    except:
                        # 处理特殊格式gif，其他格式也可这样处理
                        try:
                            os.rename(u"%s/default.gif" % self.store_dir, u"%s/%d.gif" % (real_dir, x))
                            break
                        except:
                            print 'wait for photo'
                            time.sleep(1)

                # 最后一张不用点击下一页
                if x != photo_total - 1:
                    print('移动到图片页面并点击下一页')
                    img_border = driver.find_element_by_id("js-img-border")
                    next_photo_btn = driver.find_element_by_id("js-btn-nextPhoto")
                    ActionChains(driver).move_to_element(img_border).click(next_photo_btn).perform()
                    time.sleep(1)

            # 关闭图片
            driver.find_element_by_xpath(u"//div[@class='photo_layer_close']/a").click()
            time.sleep(2)

            self.enter_photograph_page(driver)
            time.sleep(2)


    def enter_photograph_page(self, driver):
        """
        进入相册页面并切换
        """
        # 点击相册页面
        driver.find_element_by_xpath(
            u"(.//*[normalize-space(text()) and normalize-space(.)='日志'])[2]/following::a[1]").click()
        time.sleep(2)

        # 先关闭广告弹窗，不然后面会有干扰
        try:
            driver.find_element_by_id("qz_notification").find_element_by_class_name("icon-close").click()
        except:
            pass

        # 切换到相册的frame
        driver.switch_to.frame(driver.find_element_by_class_name("app_canvas_frame"))


    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e:
            return False
        return True

    def is_alert_present(self):
        try:
            self.driver.switch_to_alert()
        except NoAlertPresentException as e:
            return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally:
            self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)


if __name__ == "__main__":
    unittest.main()
