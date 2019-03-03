install:
	install -d -Dm755 . /opt/goreviewpartner
	cp -r * /opt/goreviewpartner
	install -Dm644 goreviewpartner.png /usr/share/pixmaps/goreviewpartner.png
	install -Dm644 goreviewpartner.desktop /usr/local/share/applications/goreviewpartner.desktop
