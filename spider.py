# coding:utf-8

from urllib import parse
import crawlertool as tool
from multiprocessing.dummy import Pool  # 线程池
from config import *
flag=1
def filter(str):
    str=re.sub(r'(\| India News.+)?- Times.+', '',str)
    str=re.sub(r'#|@','',str)
    str=url_extract.sub('',str)
    return str

class SpiderTwitterAccountPost(tool.abc.SingleSpider):
    """
    Twitter账号推文爬虫
    """
    def __init__(self, driver):
        self.driver = driver

    def running(self, user_name: str):


        item_list = []
        since_date = since
        #until_date=today
        # 生成请求的Url
        query_sentence = []
        query_sentence.append("from:%s" % user_name)  # 搜索目标用户发布的推文
        query_sentence.append("since:%s" % str(since_date))  # 设置开始时间
        #query_sentence.append("until:%s" % str(until_date))  # 设置结束时间
        query = " ".join(query_sentence)  # 计算q(query)参数的值
        params = {
            "q": query,
            "f": "live"
        }
        actual_url = "https://twitter.com/search?" + parse.urlencode(params)
        # self.console("实际请求Url:" + actual_url)

        # 打开目标Url
        # self.driver = webdriver.Chrome()
        self.driver.get(actual_url)
        time.sleep(3)

        while (1):
            try:
                self.driver.find_elements_by_xpath('//*[@data-testid="tweet"]')
                break
            except:
                self.driver.get(actual_url)
                time.sleep(3)
                pass

        try:
            while (1):
                tryagain = self.driver.find_element_by_css_selector(
                    "main>div>div> div> div> div> div:nth-child(2)> div> div> div> div> span")
                if "出错了" in tryagain.text:
                    tryagain.click()
                    time.sleep(3)
                else:
                    break
        except:
            pass
        # 循环遍历外层标签

        tweet_id_set = set()
        while (1):
            last_label_tweet = None
            while (1):
                try:
                    temp = self.driver.find_elements_by_xpath('//*[@data-testid="tweet"]')
                    break
                except:
                    time.sleep(1)
            for label_tweet in temp:  # 定位到推文标签

                item = {'from':user_name}
                label = label_tweet.find_element_by_css_selector(
                    "article > div > div > div > div:nth-child(2) > div:"
                    "nth-child(2) > div:nth-child(1) > div > div > div:nth-child(1) > a")
                # 读取推文ID

                if pattern := re.search("[0-9]+$", label.get_attribute("href")):
                    item["tweet_id"] = pattern.group()
                if "tweet_id" not in item:
                    self.log("账号名称:" + user_name + "|未找到推文ID标签(第" + str(len(item_list)) + "条推文)")
                    continue

                # 判断推文是否已被抓取(若未被抓取则解析推文)
                if item["tweet_id"] in tweet_id_set:
                    continue

                tweet_id_set.add(item["tweet_id"])
                last_label_tweet = label_tweet
                # 解析推文发布时间
                if label := label_tweet.find_element_by_css_selector(
                        "article > div > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div > div > div:nth-child(1) > a > time"):
                    timeOrg = datetime.datetime.strptime(
                        label.get_attribute("datetime").replace("T", " ").replace(".000Z", ""), "%Y-%m-%d %H:%M:%S")
                    deltaH = datetime.timedelta(hours=8)
                    timeRec = timeOrg + deltaH
                    item["time"] = timeRec.strftime("%Y-%m-%d %H:%M:%S")

                if label := label_tweet.find_element_by_css_selector(
                        "article > div > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1)"):
                    if "回复" in label.text and "@" in label.text:
                        if label2 := label_tweet.find_element_by_css_selector(
                                "article > div > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2)"):
                            item["text"] = label2.text
                    else:
                        # 解析推文内容
                        item["text"] = label.text

                item['text']=filter(item['text'])
                item['text']=huiche.sub('.',item['text'])
                if item['text']=='Good morning. This is the #ExpressFrontPage for today. Read more news here https://bit.ly/2m14gAR'\
                        or "You share your b'day with" in item['text']:
                    continue
                    #expressfront每日问候，非新闻

                item["url"] = url_extract.search(item['text']).group(0).strip() if url_extract.search(
                    item['text']) else ""

                item["replies"] = 0  # 推文回复数
                item["retweets"] = 0  # 推文转推数
                item["likes"] = 0  # 推文喜欢数

                # 定位到推文反馈数据标签
                if label := label_tweet.find_element_by_css_selector(
                        "article > div > div > div > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div[role='group']"):
                    if text := label.get_attribute("aria-label"):
                        # 解析推文反馈数据
                        for feedback_item in text.split("、"):
                            if "回复" in feedback_item:
                                if pattern := re.search("[0-9]+", feedback_item):
                                    item["replies"] = int(pattern.group())
                            elif "转推" in feedback_item:
                                if pattern := re.search("[0-9]+", feedback_item):
                                    item["retweets"] = int(pattern.group())
                            elif "喜欢" in feedback_item:
                                if pattern := re.search("[0-9]+", feedback_item):
                                    item["likes"] = int(pattern.group())
                # if (now-timeRec).days>0:
                #     return item_list

                item['tweet_url']='https://twitter.com/anything/status/'+item['tweet_id']
                item_list.append(item)

            # 向下滚动到最下面的一条推文
            if last_label_tweet is not None:
                self.driver.execute_script("arguments[0].scrollIntoView();", last_label_tweet)  # 滑动到推文标签
                # print("执行一次向下翻页...",self.user_name,len(item_list))
                time.sleep(3)
            else:
                # if (timeRec.date() - since_date).days <= 5:#老是意外退出
                self.driver.quit()
                break
        return item_list


def run(source):

    driver = webdriver.Chrome()
    #driver.maximize_window()
    print("Start collecting tweets from {}:".format(source))
    datas.extend(SpiderTwitterAccountPost(driver).running(source))
    print("Collection complete\n")

datas=[]
# ------------------- 单元测试 -------------------
if __name__ == "__main__":
    for nn,dir in enumerate(datadir):
        if not os.path.exists(dir):
            os.mkdir(dir)
        pool = Pool(pool_size)
        datas = []
        pool.map(run, sources[nn])
        pool.close()
        pool.join()
        wb = workbook.Workbook()  # 创建Excel对象
        ws = wb.active  # 获取当前正在操作的表对象
        # 往表中写入标题行,以列表形式写入！
        ws.append(
            ["tweet_id", 'tweet_url',"time", "text", "from", "replies", "retweets", "likes", "url",'flag'])
        for index,data in enumerate(datas):
            ws.append([data["tweet_id"],data['tweet_url'], data["time"], data["text"], data['from'],
                       data["replies"], data["retweets"], data["likes"], data["url"], index+1])
        file_path = os.path.join(dir, '{}_{}.xlsx'.format(since, today))
        wb.save(file_path)
