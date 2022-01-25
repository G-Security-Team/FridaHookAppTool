# FridaHookAppTool（以下是Hook mpass框架的例子）
mpass移动开发框架ios端抓包hook脚本



使用方法：链接数据线，开启burp设置监听端口，修改attach app名称，打开app运行脚本，开始抓包。

# mpaas移动开发框架 IDA + Frida + burp 抓包方法

- 随着市面的APP五花八门的加固手段越来越多，对渗透测试人员测试APP时构成了极大的困扰，常用的抓包方法现在基本已经无法抓取到明文数据包，大多数APP使用通信加密的方式来进行隐藏自己的数据流量，从而导致就算渗透测试人员截取到了对应的数据包，也无法理解其中的内容，无法对APP进行漏洞挖掘，为此我在网络上参考学习了一段时间，得到了一种十分通用的抓包改包方法。
-  大家都知道，当一个APP的数据流量加密之后我们在抓包软件中看到的是密文形式，若要想解密->修改->加密这个过程并不容易，甚至需要对APP深入逆向才能解密出明文，那么换个思路，我们可不可以越过加解密过程直接去寻找明文数据呢？答案是肯定的，hook为我们带来了十分开阔的解密思路，不需要逆向出加密算法只需要在送入加密函数之前将明文数据hook住，再其上最修改，再送入加密函数，便可以达到修改数据包的目的。
-  现在的加固方式多种多样，但是我们这样来看，移动APP测试无非就是安卓阵营和IOS阵营，几乎所有的加固方式都是针对安卓阵营的，IOS极少会有，原因是Appstore对APP的审核非常严格，导致IOS应用加固后面临无法上架应用商店的问题。回过头来看，移动端测试可以拆解为Android客户端、IOS客户端、服务端三个部分来进行测试，所以在测试服务端的时候，我们尽可能的选择IOS APP来进行服务端的检测（虽然OC没有明显调用关系），下面我给大家举的实战的例子就是IOS APP中如何通过一种特定的思路甚至大部分代码都不需要变动的方式来抓取明文数据包。
-  Mpaas是蚂蚁金服的移动开发平台，使用该架构开发的应用在测试过程中发现根本无法抓取到业务通信数据包，这比加密数据做的更绝，既然渗透测试人员通过设置HTTP代理的方式对应用进行测试，那干脆就不使用HTTP通讯协议，但是使用该方法依旧可以对mpaas应用进行正常渗透测试。
-  本片文章用到的技术主要是HOOK，工具主要是Frida、Frida-ios-dump、BurpSuite。
-  本文章不会细致说明某项技术及工具的详细用法（客户授权测试APP，同是mpaas脚本完成后测试了一把支**）

#### 一、	首先将需要测试的APP在已经越狱的手机中安装，然后运行该APP，数据线连接电脑命令行使用命令 “frida-ps -U” 查看frida环境是否正常
  
![MpaasPentestTool](1.png)
#### 二、	使用frida-ios-dump 进行砸壳
  
![MpaasPentestTool](2.png)
#### 三、	使用解压文件解压生成的ipa文件，按文件大小排序，一般最大的就是Unix可执行文件。
  
![MpaasPentestTool](3.png)
#### 四、	将该文件拖入IDA，寻找明文数据位置，通常在字符串中搜索request、response等关键字进行第一步的模糊查找工作，找到可疑的类可以先记录下来，一般带有request等关键字的类或方法都是用来发送请求的，IDA寻找过程略，这里我找到了：DTURLRequestOperation
  
![MpaasPentestTool](4.png)
#### 五、	使用frida-trace 跟踪该类的所有方法，这时使APP发送数据包，如果过程中调用了你跟踪的类，就会打印出调用堆栈，在其中寻找可能跟发送请求传送数据有关的方法，这里我找到了：-[DTURLRequestOperation addHTTPBodyParameter:0x102bc0a20 forKey:0x102bc0ec0]
  
![MpaasPentestTool](5.png)
#### 六、	在执行frida-trace的目录下有__handlers__文件夹，在该文件夹下有frida已经选择hook的所有方法，每个方法对应一个js（frida是利用js来进行hook的，若有初学者可先学习一下frida）。找到[DTURLRequestOperation addHTTPBodyParameter:forKey:]该方法的js，编辑修改使frida打印出该方法的输入参数值与类型:
  
![MpaasPentestTool](6.png)
#### 七、	运行 frida-trace 查看，hook到了对应的请求（不要在意那串长的字符串，那是base64，最终这些数据会映射到burp里不要担心）
  
![MpaasPentestTool](7.png)
#### 八、	发送数据包明文位置已经找到了，接受数据包必然会变成明文，才能正常进入业务逻辑，这里我也已经知道了response明文的位置 [DTURLRequestOperation responseString]，过程略，刚才hook的是输入参数，这个方法hook的返回值
  
![MpaasPentestTool](8.png)
  
![MpaasPentestTool](8(1).png)
#### 九、	现在到了比较关键的一步，就是我们现在用frida hook到了APP的明文数据，那么如何进行渗透测试呢？这个问题很简单，frida已经给我们准备好了，怎么做？看下面：
- 使用python启动一个镜像http服务器 我的端口起在28080（就是发什么回什么的服务器）
  
![MpaasPentestTool](9.png)
  
![MpaasPentestTool](9(1).png)
- 构建python脚本，在脚本中使用frida hook到数据（hook到的数据在js中），发送给python，并且接受python回传的数据替换原来参数的值。
  
![MpaasPentestTool](9(2).png)
- python从js中获取hook到的明文数据，使用requests将明文数据作为http请求的body发送至127.0.0.1:28080，也就是镜像服务器，并且设置代理为burp的8080（这样burp就能抓到明文数据了，并且可以修改）
  
![MpaasPentestTool](9(3).png)
- 将requests的返回值也就镜像服务器返回回来的你修改过的数据包，赋给原来的变量，APP的业务逻辑会继续运行。
#### 十、	整理思路至此，其实就可以正常的抓包改包了，只需要运行着该脚本，就像挂着代理一样burp发挥他应有的功能。（不要拔掉数据线哦哈哈）
  
![MpaasPentestTool](10.png)
#### 十一、	思路理清楚之后，其实主要的难点在于找到到hook点以及OC与JS之间的数据类型转换，尽量寻找NSString类型的方法参数或者是返回值，这样修改起来出错的可能比较小，当然复杂数据类型也可以进行hook，frida是个十分强大的hook工具，官方提供了说明文档对于复杂类型的数据类型转换：
- OC字典转JS Json：
  
![MpaasPentestTool](11.png)
- JS Json转OC 字典：
  
![MpaasPentestTool](11(1).png)
#### 十二、	效果图 随便修改一下数据包证明是可以修改的
  
![MpaasPentestTool](12.png)
  
![MpaasPentestTool](12(1).png)
- 按照此类方法，只要hook到明文数据，稍微简单修改一下代码中的js部分，再结合burp就可以愉快的进行渗透测试喽，再也不用去管什么加密不加密，协议不协议。不过从我已经完成这个hook代码目前看来是通杀mpaas的，尝试了三款mpaas app均可正常抓包改包，只需要替换attach的app名称即可。


- 邮箱:jiaxingl@126.com
- Github: https://github.com/lijiaxing1997
