iperform
========

Whatsapp chatbot sending choreographic instructions to dancers through bash scripts. Built on top of [Yowsup](https://github.com/tgalal/yowsup).

## Setup

`git clone` this repo. Do not install Yowsup through `pip install yowsup2`, as you often have to manually patch the library because of Whatsapp’s new API changes. Yowsup is not an official whatsapp client, after all, so hacking is mandatory.

From your project’s root folder:

	cd yowsup
	sudo python setup.py install

to install all dependencies.

### Registration of a new number

Register a new Whatsapp number and get a registration code as password. As of June 2016, use this syntax:

	cd yowsup
	sudo yowsup-cli registration --env android --requestcode sms -p (your phone number without + or 00) --cc xx --mcc xxx --mnc xx -r voice --debug

* [check this](https://github.com/tgalal/yowsup/wiki/yowsup-cli-2.0#yowsup-cli-registration) to look up the `--cc`, `--mcc` and `--mnc` of your phone number.
* using `-r voice` is the most viable way to actually receive a registration code from Whatsapp, through a voice bot.
* adding `--debug` let you see what’s going on in case of problems.

Once you get your registration code, do

	sudo yowsup-cli registration --env android --register xxxxxx  -p xxxxxxxxxxx --cc xx

The current repo has a patch to work with `--env android`, that replaces `env_android.py` in `yowsup/yowsup/env` with an updated version that you can [find here](https://github.com/colonyhq/yowsup/blob/master/yowsup/env/env_android.py) (see [this](https://github.com/tgalal/yowsup/issues/2062)).

After you can:

* add your bot’s phone number and password in `server.py` ([line 24 and 25](https://github.com/hackersanddesigners/iperform/blob/master/server.py#L24)) and in `layer.py` ([line 25](https://github.com/hackersanddesigners/iperform/blob/master/layer.py#L25))
* then run `python server.py` from your project’s root folder.

## Commands

While running `python server.py`, open a new terminal session and use the following commands to trigger the desired action:

**Send message to number**

	curl --data-urlencode 'num=xxx' --data-urlencode 'msg=text here' 'http://localhost:8000/send-msg'

**Send message to group**

	curl --data-urlencode 'group-id=xxx-ttt' --data-urlencode 'msg=does this work' 'http://localhost:8000/group-msg'

**Create and invite to group**

	curl 'http://localhost:8000/group-create?group-name=uu&nums=xxx,xxx'	

**Invite to group**

	curl 'http://localhost:8000/group-invite?group-id=xxx-ttt&nums=xxx,xxx'	

### Info

You can grab the `group-id` of a Whatsapp group from the terminal debug output of `python server.py`, right after you created a new whatsapp group: it looks something like `31627060041-1010124455@g.us`:

* the first bunch of numbers correspond to the whatsapp number which created the group, 
* whereas the second is the timestamp of when the group was created. 

You only need the two series of numbers—`31627060041-1010124455`.

As a general comment, be aware that the program might stop working as Whatsapp changes its API. Look up the [/issues](https://github.com/tgalal/yowsup/issues) section of Yowsup, to catch up on the latest news.