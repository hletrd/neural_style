from flask import Flask, request, redirect, send_from_directory
import random
import string
from pymongo import MongoClient
from time import gmtime, strftime
import os
import subprocess
import threading
import imghdr
import math
import config

dbclient = MongoClient('127.0.0.1', 27017)
db = dbclient.db_neural
col = db.images

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/hletrd/neural-run/files/'

gpu = "-1"
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
processing = False
t = False
col.update_many({"queued": False, "status": False}, {"$set": {"queued": True}})

class t_run(threading.Thread):
	def __init__(self, url, cweight, sweight, tweight, lrate, ni):
		threading.Thread.__init__(self)
		global processing
		processing = True
		self.url = str(url)
		self.cweight = str(cweight)
		self.sweight = str(sweight)
		self.tweight = str(tweight)
		self.lrate = str(lrate)
		self.ni = str(ni)

	def run(self):
		os.chdir('/home/hletrd/neural-style/')
		self.p = subprocess.call(["th", "neural_style.lua", "-style_image", app.config['UPLOAD_FOLDER'] + self.url + "_style.jpg", "-content_image", app.config['UPLOAD_FOLDER'] + self.url + "_content.jpg", "-gpu", gpu, "-output_image", app.config['UPLOAD_FOLDER'] + self.url + "_out.png", "-image_size", "384", "-optimizer", "lbfgs", "-content_weight", self.cweight, "-style_weight", self.sweight, "-tv_weight", self.tweight, "-num_iterations", self.ni])
		global processing
		processing = False


@app.route('/')
def index():
	return """<!doctype HTML>
<html>
<head>
	<meta charset="utf-8">
	<title>Neural Style Online</title>
	<link rel="stylesheet" href="/files/normalize.css">
	<link rel="stylesheet" href="/files/skeleton.css">
	<style type="text/css">
	.u-full-width {
		height: 30px !important;
	}
	</style>
</head>
<body>
	<div class="container">
	<h4>Web-based neural image styling by HLETRD</h4>
	<form method="POST" action="/submit" enctype="multipart/form-data">
	<p>This service is based on <a href="https://github.com/jcjohnson/neural-style/">Torch implementation of neural style algorithm</a> by jcjohnson.</p>
	<p>Only jpg files are allowed. Maximum allowed size is 8MB totally.</p>
	<hr>
	<h5>Select images</h5>
	<div class="row"><p class="six columns">Select style image</p><input class="six columns" name="style" type="file"></div>
	<div class="row"><p class="six columns">Select content image</p><input class="six columns" name="content" type="file"></div>
	<h5>Set optional parameters</h5>
	<div class="row"><p class="eight columns">Input number of iterations(min: 1, max: 1000): </p><input class="u-full-width four columns" name="ni" type="text" value="300"></div>
	<div class="row"><p class="eight columns">Input content weight(How much to weight the content reconstruction term.)</p><input class="u-full-width four columns" name="cweight" type="text" value="5"></div>
	<div class="row"><p class="eight columns">Input style weight(How much to weight the style reconstruction term.)</p><input class="u-full-width four columns" name="sweight" type="text" value="100"></div>
	<div class="row"><p class="eight columns">Input tv weight(Weight of total-variation (TV) regularization; this helps to smooth the image.)</p><input class="u-full-width four columns" name="tweight" type="text" value="0.001"></div>
	<!--<div class="row"><p class="eight columns">Input learning rate(Learning rate to use with the ADAM optimizer.)</p><input class="u-full-width four columns" name="lrate" type="text" value="1"></div>-->
	<hr>
	<input class="button-primary" type="submit" value="Submit images">
	</form>
	<div style="height: 20px"></div>
	<ul>
		<li>Please do not upload too many files.</li>
		<li>Please do not upload explicit photos.</li>
		<li>If your result is hard to recognize, try increasing number of iterations.</li>
		<li><a href="https://github.com/hletrd/neural_style">This project on GitHub</a></li>
	</ul>
	<a href="/list">List of uploaded files</a>
	<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-36880204-4', 'auto');
  ga('send', 'pageview');
	</script>
	</div>
</body>
</html>"""

@app.route('/submit', methods=['POST'])
def submit():
	style = request.files['style']
	content = request.files['content']
	cweight = float(request.form['cweight'])
	sweight = float(request.form['sweight'])
	tweight = float(request.form['tweight'])
	#lrate = float(request.form['lrate'])
	ni = int(request.form['ni'])
	if ni > 1000:
		ni = 1000
	elif ni < 1:
		ni = 1
	if style and content:
		url = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(8))
		style.save(os.path.join(app.config['UPLOAD_FOLDER'], url + '_style.jpg'))
		content.save(os.path.join(app.config['UPLOAD_FOLDER'], url + '_content.jpg'))
		if imghdr.what(os.path.join(app.config['UPLOAD_FOLDER'], url + '_style.jpg')) == 'jpeg' and imghdr.what(os.path.join(app.config['UPLOAD_FOLDER'], url + '_content.jpg')) == 'jpeg':
			col.insert_one({"url": url, "status": False, "uploaded": strftime("%Y-%m-%d %H:%M:%S", gmtime()), "queued": True, "cweight": cweight, "sweight": sweight, "tweight": tweight, "lrate": lrate, "ni": ni})
			return redirect('/list')
		else:
			return '<!doctype HTML><html><head><title>Error</title></head><body>error: not a valid JPEG file.</body></html>'
	else:
		return '<!doctype HTML><html><head><title>Error</title></head><body>error: please check filetype or filesize.</body></html>'

@app.route('/delete/' + config.password + '/<url>')
def delete(url):
	try:
		os.remove(app.config['UPLOAD_FOLDER'] + url + '_style.jpg')
		os.remove(app.config['UPLOAD_FOLDER'] + url + '_content.jpg')
		os.remove(app.config['UPLOAD_FOLDER'] + url + '_out.png')
	except:
		print 'err'
	col.remove({"url": url})
	return redirect('/list')

@app.route('/list')
@app.route('/list/<int:page>')
def list(page=1):
	result = ''
	unprocessed_list = col.find({"status": False})
	for i in unprocessed_list:
		if os.path.isfile(app.config['UPLOAD_FOLDER'] + i['url'] + '_out.png'):
			col.update({"url": i['url']}, {"$set": {"status": True}}, upsert=False)
	for i in col.find().sort("uploaded", -1).skip((page - 1) * 10).limit(10):
		if i['status']:
			result = result + '<div><a href="/image/' + i['url'] + '">' + i['url'] + '</a>: Processing completed, uploaded at ' + i['uploaded'] + ' GMT, <br /><img alt="" src="/files/' + i['url'] + '_out.png" width="250"></div>'
		else:
			if 'queued' in i and i['queued']:
				result = result + '<div><a href="/image/' + i['url'] + '">' + i['url'] + '</a>: Queued now... uploaded at ' + i['uploaded'] + ' GMT</div>'
			else:
				result = result + '<div><a href="/image/' + i['url'] + '">' + i['url'] + '</a>: Processing now... uploaded at ' + i['uploaded'] + ' GMT, processing started at ' + i['pstarted'] + ' GMT</div>'
	lastpage = math.ceil(1.0 * col.count() / 10)
	pagelist = ''
	if page > 2:
		pagelist += '<a href="/list/' + str(page - 2) + '">' + str(page - 2) + '</a> '
	if page > 1:
		pagelist += '<a href="/list/' + str(page - 1) + '">' + str(page - 1) + '</a> '
	pagelist += str(page) + ' '
	if lastpage >= page+1:
		pagelist += '<a href="/list/' + str(page + 1) + '">' + str(page + 1) + '</a> '
	if lastpage >= page+2:
		pagelist += '<a href="/list/' + str(page + 2) + '">' + str(page + 2) + '</a> '
	return """<!doctype HTML>
	<html>
	<head>
		<meta charset="utf-8">
		<title>List</title>
		<link rel="stylesheet" href="/files/normalize.css">
		<link rel="stylesheet" href="/files/skeleton.css">
	</head>
	<body><div class="container">""" + result + '<hr><span style="font-size: 1.2em">' + pagelist + '</span><hr><a href="/">Back</a>' + """<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-36880204-4', 'auto');
  ga('send', 'pageview');
	</script>""" + '</div></body></html>'

@app.route('/image/<url>')
def image(url):
	an_image = col.find_one({"url": url})
	if an_image:
		result = """<!doctype HTML>
		<head>
			<meta charset="utf-8">
			<title>Image</title>
			<link rel="stylesheet" href="/files/normalize.css">
			<link rel="stylesheet" href="/files/skeleton.css">
		</head>
		<body>
		<div class="container">
		<h4>style</h4>
		<img alt="" src="/files/""" + url + """_style.jpg" width="512">
		<hr>
		<h4>content</h4>
		<img alt="" src="/files/""" + url + """_content.jpg" width="512">
		<hr>
		<h4>result</h4>
		<img alt="" src="/files/""" + url + """_out.png" width="512">
		<hr>"""
		if 'ni' in an_image:
			result += "<h5>Number of iterations: " + an_image['ni'] + "</h5><h5>Content weight: " + an_image['cweight'] + "</h5><h5>Style weight: " + an_image['sweight'] + "</h5><h5>Tv weight: " + an_image['tweight'] + "</h5><hr>"
		result += """<a class="button-primary" href="#" onclick="history.go(-1)">Back</a>
		<script>
	  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
	  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
	  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
	  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
	  ga('create', 'UA-36880204-4', 'auto');
	  ga('send', 'pageview');
		</script>
		</div>
		</body>
		</html>"""
	else:
		result = "error"
	return result

@app.route('/files/<path:path>')
def staticfile(path):
	return send_from_directory(app.config['UPLOAD_FOLDER'], path, as_attachment=False)

def timer():
	threading.Timer(3.0, timer).start()
	global processing
	if processing == False:
		try:
			a = col.find({"queued": True}).sort("uploaded", 1).limit(1).next()
			if a:
				global t
				t = t_run(a['url'], a['cweight'], a['sweight'], a['tweight'], a['lrate'], a['ni'])
				t.start()
				col.update({"url": a['url']}, {"$set": {"queued": False, "pstarted": strftime("%Y-%m-%d %H:%M:%S", gmtime())}}, upsert=False)
		except:
			a = 1

threading.Timer(3.0, timer).start()

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port=9002, use_reloader=False)