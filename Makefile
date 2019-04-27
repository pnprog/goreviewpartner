install:
	install -d -Dm755 . /opt/goreviewpartner
	cp -rp * /opt/goreviewpartner
	chmod a+w /opt/goreviewpartner/config.ini
	install -Dm644 goreviewpartner.png /usr/share/pixmaps/goreviewpartner.png
	install -Dm644 goreviewpartner.desktop /usr/local/share/applications/goreviewpartner.desktop
