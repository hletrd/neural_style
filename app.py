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
app.config['UPLOAD_FOLDER'] = config.upload_folder

app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
processing = False
t = False
col.update_many({"queued": False, "status": False}, {"$set": {"queued": True}})

class t_run(threading.Thread):
	def __init__(self, url, cweight, sweight, tweight, ni, isize, styletype, styletext):
		threading.Thread.__init__(self)
		global processing
		processing = True
		self.url = str(url)
		self.cweight = str(cweight)
		self.sweight = str(sweight)
		self.tweight = str(tweight)
		self.ni = str(ni)
		self.isize = str(isize)
		self.styletype = str(styletype)
		self.styletext = str(styletext)

	def run(self):
		os.chdir('/home/hletrd/neural/neural-style/')
		if self.styletype == "1":
			self.p = subprocess.call(["th", "neural_style.lua", "-style_image", app.config['UPLOAD_FOLDER'] + self.url + "_style.jpg", "-content_image", app.config['UPLOAD_FOLDER'] + self.url + "_content.jpg", "-gpu", config.gpu, "-output_image", app.config['UPLOAD_FOLDER'] + self.url + "_out.png", "-image_size", self.isize, "-optimizer", "lbfgs", "-backend", config.backend, "-content_weight", self.cweight, "-style_weight", self.sweight, "-tv_weight", self.tweight, "-num_iterations", self.ni, "-save_iter", "0", "-print_iter", "0", "-cudnn_autotune"])
		elif self.styletype == "0":
			self.p = subprocess.call(["th", "neural_style.lua", "-style_image", app.config['UPLOAD_FOLDER'] + self.styletext + "_style.jpg", "-content_image", app.config['UPLOAD_FOLDER'] + self.url + "_content.jpg", "-gpu", config.gpu, "-output_image", app.config['UPLOAD_FOLDER'] + self.url + "_out.png", "-image_size", self.isize, "-optimizer", "lbfgs", "-backend", config.backend, "-content_weight", self.cweight, "-style_weight", self.sweight, "-tv_weight", self.tweight, "-num_iterations", self.ni, "-save_iter", "0", "-print_iter", "0", "-cudnn_autotune"])
		global processing
		processing = False


@app.route('/')
def index():
	return """<!doctype HTML>
<html>
<head>
	<meta charset="utf-8">
	<meta id="viewport" name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
	<title>Neural Style Online</title>
	<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js"></script>
	<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
	<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-36880204-4', 'auto');
  ga('send', 'pageview');
	</script>
	<style type="text/css">
	.spacer{
	height: 10px;
	}
	</style>
	<script>
	function sets(d){
		$("#style").val(d.dataset.id);
		if (d.dataset.id == -1){
			$("#style-file").css('display', 'block');
		} else {
			$("#style-file").css('display', 'none');
		}
		$("#select").html(d.innerHTML);
	}
	</script>
</head>
<body>
	<nav class="navbar navbar-default">
		<div class="container">
			<div class="navbar-header">
				<button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
				<span class="sr-only">Toggle navigation</span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				</button>
				<a class="navbar-brand" href="/">Neural artistic styling</a>
			</div>
			<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
				<ul class="nav navbar-nav">
				<li class="active"><a href="/">Upload new image</a></li>
				<li><a href="/list">List of uploaded images</a></li>
				</ul>
				<ul class="nav navbar-nav navbar-right">
				<li><a href="https://0101010101.com">Created by HLETRD</a></li>
				</ul>
			</div>
		</div>
	</nav>
	<div class="container">
	<form method="POST" action="/submit" enctype="multipart/form-data" class="form-horizontal">
	<p>This service is based on <a href="https://github.com/jcjohnson/neural-style/">Torch implementation of neural style algorithm</a> by jcjohnson.</p>
	<p>Only jpg files are allowed. Maximum allowed size is 8MB totally.</p>
	<hr>
	<strong>Select images</strong>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Select style image</div><div class="col-md-8"><div class="btn-group">
		<button type="button" class="btn btn-default" id="select">Select style</button>
		<button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
		<span class="caret"></span>
		<span class="sr-only">Toggle Dropdown</span>
		</button>
		<ul class="dropdown-menu">
		<li><a href="#" onclick="sets(this)" data-id="0">The Starry Night</a></li>
		<li><a href="#" onclick="sets(this)" data-id="1">Shipwreck</a></li>
		<li><a href="#" onclick="sets(this)" data-id="2">The Scream</a></li>
		<li><a href="#" onclick="sets(this)" data-id="3">Seated Nude</a></li>
		<li><a href="#" onclick="sets(this)" data-id="4">Ink wash</a></li>
		<li><a href="#" onclick="sets(this)" data-id="5">Hand with Reflecting Sphere</a></li>
		<li><a href="#" onclick="sets(this)" data-id="6">Woman with a Hat</a></li>
		<li><a href="#" onclick="sets(this)" data-id="7">Picasso self 1907</a></li>

		<li role="separator" class="divider"></li>
		<li><a href="#" onclick="sets(this)" data-id="-1">Use custom pic</a></li>
		</ul>
	</div>
	<div class="spacer"></div>
	<input type="hidden" name="style_select" id="style" value="999">
	<input class="form-control" name="style" type="file" style="display: none;" id="style-file"></div>
	<div class="col-md-8 col-md-offset-4">Choose a image with artistic style. Images from famous artists are recommended.<br />(Examples: The Starry Night, The Scream.)</div></div>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Select content image</div><div class="col-md-8"><input class="form-control" name="content" type="file"></div>
	<div class="col-md-8 col-md-offset-4">Choose a image that you want to repaint with artistic style.</div></div>
	<hr>
	<strong>Set optional parameters</strong>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Input number of iterations</div><div class="col-md-8"><input class="form-control" name="ni" type="text" value="500"></div>
	<div class="col-md-8 col-md-offset-4">Min: 1, Max: 1000. Increasing the value may increase overall quality of the image.</div></div>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Input content weight</div><div class="col-md-8"><input class="form-control" name="cweight" type="text" value="5"></div>
	<div class="col-md-8 col-md-offset-4">How much to weight the content reconstruction term.</div></div>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Input style weight</div><div class="col-md-8"><input class="form-control" name="sweight" type="text" value="100"></div>
	<div class="col-md-8 col-md-offset-4">How much to weight the style reconstruction term.</div></div>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Input tv weight</div><div class="col-md-8"><input class="form-control" name="tweight" type="text" value="0.001"></div>
	<div class="col-md-8 col-md-offset-4">Weight of total-variation (TV) regularization; this helps to smooth the image.</div></div>
	<div class="spacer"></div>
	<div class="row"><div class="col-md-4">Input result image size</div><div class="col-md-8"><input class="form-control" name="isize" type="text" value="512"></div>
	<div class="col-md-8 col-md-offset-4">Size of long side of the result image in pixels. Max: 1000</div></div>
	<!--<div class="row"><p class="eight columns">Input learning rate(Learning rate to use with the ADAM optimizer.)</p><input class="u-full-width four columns" name="lrate" type="text" value="1"></div>-->
	<div class="spacer"></div>
	<div class="row"><div class="col-md-2 col-md-offset-4"><input class="btn-block btn btn-primary" type="submit" value="Submit images"></div></div>
	</form>
	<hr>
	<ul>
		<li>Please do not upload too many files.</li>
		<li>Please do not upload explicit photos.</li>
		<li>If your result is hard to recognize, try increasing number of iterations.</li>
		<li><a href="https://github.com/hletrd/neural_style">This project on GitHub</a></li>
	</ul>
	</div>
</body>
</html>"""

@app.route('/submit', methods=['POST'])
def submit():
	style_selected = int(request.form['style_select'])
	url = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
	style = False
	if style_selected == 0:
		styletype = 0
		styletext = "starry_night"
	elif style_selected == 1:
		styletype = 0
		styletext = "shipwreck"
	elif style_selected == 2:
		styletype = 0
		styletext = "the_scream"
	elif style_selected == 3:
		styletype = 0
		styletext = "seated_nude"
	elif style_selected == 4:
		styletype = 0
		styletext = "ink_wash"
	elif style_selected == 5:
		styletype = 0
		styletext = "escher_sphere"
	elif style_selected == 6:
		styletype = 0
		styletext = "woman_with_a_hat"
	elif style_selected == 7:
		styletype = 0
		styletext = "picasso_selfport1907"
	elif style_selected == -1 or not style:
		styletype = 1
		styletext = ''
		style = request.files['style']
		style.save(os.path.join(app.config['UPLOAD_FOLDER'], url + '_style.jpg'))
		if imghdr.what(os.path.join(app.config['UPLOAD_FOLDER'], url + '_style.jpg')) != 'jpeg':
			return '<!doctype HTML><html><head><title>Error</title></head><body>error: not a valid JPEG file.</body></html>'
	else:
		return '<!doctype HTML><html><head><title>Error</title></head><body>error: invalid style.</body></html>'

	content = request.files['content']
	cweight = float(request.form['cweight'])
	sweight = float(request.form['sweight'])
	tweight = float(request.form['tweight'])
	#lrate = float(request.form['lrate'])
	ni = int(request.form['ni'])
	isize = int(request.form['isize'])
	if isize > 1024:
		isize = 1024
	elif isize < 1:
		isize = 1
	if ni > 1000:
		ni = 1000
	elif ni < 1:
		ni = 1
	if content:
		content.save(os.path.join(app.config['UPLOAD_FOLDER'], url + '_content.jpg'))
		if imghdr.what(os.path.join(app.config['UPLOAD_FOLDER'], url + '_content.jpg')) == 'jpeg':
			col.insert_one({"url": url, "status": False, "uploaded": strftime("%Y-%m-%d %H:%M:%S", gmtime()), "queued": True, "cweight": cweight, "sweight": sweight, "tweight": tweight, "ni": ni, "isize": isize, "styletype": styletype, "styletext": styletext})
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
			result = result + '<div class="list-group"><a class="list-group-item" href="/image/' + i['url'] + '"><h4 class="list-group-item-heading">' + i['url'] + '</h4><p class="list-group-item-text">Processing completed, uploaded at ' + i['uploaded'] + ' GMT</p><div class="thumbnail"><img alt="" src="/files/' + i['url'] + '_out.png" width="250"></div></div>'
		else:
			if 'queued' in i and i['queued']:
				result = result + '<div class="list-group"><a class="list-group-item" href="/image/' + i['url'] + '"><h4 class="list-group-item-heading">' + i['url'] + '</h4><p class="list-group-item-text">Queued now... uploaded at ' + i['uploaded'] + ' GMT</p></div>'
			else:
				result = result + '<div class="list-group"><a class="list-group-item" href="/image/' + i['url'] + '"><h4 class="list-group-item-heading">' + i['url'] + '</h4><p class="list-group-item-text">Processing now... uploaded at ' + i['uploaded'] + ' GMT, processing started at ' + i['pstarted'] + ' GMT</p></div>'
	lastpage = math.ceil(1.0 * col.count() / 10)
	pagelist = ''
	if page > 6:
		pagelist += '<li><a href="/list/1"><span>&laquo;</span></a></li>'
	if page > 5:
		pagelist += '<li><a href="/list/' + str(page - 5) + '">' + str(page - 5) + '</a></li>'
	if page > 4:
		pagelist += '<li><a href="/list/' + str(page - 4) + '">' + str(page - 4) + '</a></li>'
	if page > 3:
		pagelist += '<li><a href="/list/' + str(page - 3) + '">' + str(page - 3) + '</a></li>'
	if page > 2:
		pagelist += '<li><a href="/list/' + str(page - 2) + '">' + str(page - 2) + '</a></li>'
	if page > 1:
		pagelist += '<li><a href="/list/' + str(page - 1) + '">' + str(page - 1) + '</a></li>'
	pagelist += '<li class="active"><a href="#">' + str(page) + '</a></li>'
	if lastpage >= page+1:
		pagelist += '<li><a href="/list/' + str(page + 1) + '">' + str(page + 1) + '</a></li>'
	if lastpage >= page+2:
		pagelist += '<li><a href="/list/' + str(page + 2) + '">' + str(page + 2) + '</a></li>'
	if lastpage >= page+3:
		pagelist += '<li><a href="/list/' + str(page + 3) + '">' + str(page + 3) + '</a></li>'
	if lastpage >= page+4:
		pagelist += '<li><a href="/list/' + str(page + 4) + '">' + str(page + 4) + '</a></li>'
	if lastpage >= page+5:
		pagelist += '<li><a href="/list/' + str(page + 5) + '">' + str(page + 5) + '</a></li>'
	if lastpage >= page+6:
		pagelist += '<li><a href="/list/' + str(int(lastpage)) + '"><span>&raquo;</span></li>'
	return """<!doctype HTML>
<html>
<head>
	<meta charset="utf-8">
	<meta id="viewport" name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
	<title>Neural Style Online</title>
	<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js"></script>
	<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
	<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-36880204-4', 'auto');
  ga('send', 'pageview');
	</script>
	<style type="text/css">
	.spacer{
	height: 10px;
	}
	</style>
</head>
<body>
	<nav class="navbar navbar-default">
		<div class="container">
			<div class="navbar-header">
				<button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
				<span class="sr-only">Toggle navigation</span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				</button>
				<a class="navbar-brand" href="/">Neural artistic styling</a>
			</div>
			<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
				<ul class="nav navbar-nav">
				<li><a href="/">Upload new image</a></li>
				<li class="active"><a href="/list">List of uploaded images</a></li>
				</ul>
				<ul class="nav navbar-nav navbar-right">
				<li><a href="https://0101010101.com">Created by HLETRD</a></li>
				</ul>
			</div>
		</div>
	</nav>
	<div class="container">""" + result + '<hr><div class="text-center"><nav><ul class="pagination">' + pagelist + '</ul></nav>' + """<script>
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
		if an_image['styletype'] == 0:
			aaaaaa = an_image['styletext']
		else:
			aaaaaa = url
		result = """<!doctype HTML>
<html>
<head>
	<meta charset="utf-8">
	<meta id="viewport" name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
	<title>Neural Style Online</title>
	<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
	<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.2.4/jquery.min.js"></script>
	<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
	<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-36880204-4', 'auto');
  ga('send', 'pageview');
	</script>
	<style type="text/css">
	.spacer{
	height: 10px;
	}
	</style>
</head>
<body>
	<nav class="navbar navbar-default">
		<div class="container">
			<div class="navbar-header">
				<button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
				<span class="sr-only">Toggle navigation</span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				<span class="icon-bar"></span>
				</button>
				<a class="navbar-brand" href="/">Neural artistic styling</a>
			</div>
			<div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
				<ul class="nav navbar-nav">
				<li><a href="/">Upload new image</a></li>
				<li><a href="/list">List of uploaded images</a></li>
				<li class="active"><a href="#">Image: """ + url + """</a></li>
				</ul>
				<ul class="nav navbar-nav navbar-right">
				<li><a href="https://0101010101.com">Created by HLETRD</a></li>
				</ul>
			</div>
		</div>
	</nav>
	<div class="container">
		<h4>style</h4>
		<img alt="" src="/files/""" + aaaaaa + """_style.jpg" width="512">
		<hr>
		<h4>content</h4>
		<img alt="" src="/files/""" + url + """_content.jpg" width="512">
		<hr>
		<h4>result</h4>
		<img alt="" src="/files/""" + url + """_out.png" width="512">
		<hr>"""
		if 'ni' in an_image:
			result += "<h5>Number of iterations: " + str(an_image['ni']) + "</h5><h5>Content weight: " + str(an_image['cweight']) + "</h5><h5>Style weight: " + str(an_image['sweight']) + "</h5><h5>Tv weight: " + str(an_image['tweight']) + "</h5><hr>"
		result += """<a class="btn btn-primary" href="#" onclick="history.go(-1)">Back</a>
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
		result = "<!doctype HTML><html><head><title>Error</title></head><body>404 not found</body></html>"
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
				t = t_run(a['url'], a['cweight'], a['sweight'], a['tweight'], a['ni'], a['isize'], a['styletype'], a['styletext'])
				t.start()
				col.update({"url": a['url']}, {"$set": {"queued": False, "pstarted": strftime("%Y-%m-%d %H:%M:%S", gmtime())}}, upsert=False)
		except:
			a = 1

threading.Timer(3.0, timer).start()

if __name__ == '__main__':
	app.run(debug=True, host="0.0.0.0", port=9002, use_reloader=False)