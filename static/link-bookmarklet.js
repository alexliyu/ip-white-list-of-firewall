(function() {
    var h = true,
    i = null,
    j = false,
    k, aa = "/admin/Link_bookmarklet";
    var q = this;
    function s() {}
    function t(a) {
	var b = typeof a;
	if (b == "object") if (a) {
	    if (a instanceof Array || !(a instanceof Object) && Object.prototype.toString.call(a) == "[object Array]" || typeof a.length == "number" && typeof a.splice != "undefined" && typeof a.propertyIsEnumerable != "undefined" && !a.propertyIsEnumerable("splice")) return "array";
	    if (! (a instanceof Object) && (Object.prototype.toString.call(a) == "[object Function]" || typeof a.call != "undefined" && typeof a.propertyIsEnumerable != "undefined" && !a.propertyIsEnumerable("call"))) return "function"
	} else return "null";
	else if (b == "function" && typeof a.call == "undefined") return "object";
	return b
    }
    function ba(a) {
	if (a.hasOwnProperty && a.hasOwnProperty(v)) return a[v];
	a[v] || (a[v] = ++ca);
	return a[v]
    }
    var v = "closure_uid_" + Math.floor(Math.random() * 2147483648).toString(36),
    ca = 0;
    function da(a, b) {
	var c = b || q;
	if (arguments.length > 2) {
	    var d = Array.prototype.slice.call(arguments, 2);
	    return function() {
		var f = Array.prototype.slice.call(arguments);
		Array.prototype.unshift.apply(f, d);
		return a.apply(c, f)
	    }
	} else return function() {
	    return a.apply(c, arguments)
	}
    }
    function ea(a) {
	var b = Array.prototype.slice.call(arguments, 1);
	return function() {
	    var c = Array.prototype.slice.call(arguments);
	    c.unshift.apply(c, b);
	    return a.apply(this, c)
	}
    }
    function w(a, b) {
	function c() {}
	c.prototype = b.prototype;
	a.B = b.prototype;
	a.prototype = new c
    }
    function fa(a) {
	for (var b = 1; b < arguments.length; b++) {
	    var c = String(arguments[b]).replace(/\$/g, "$$$$");
	    a = a.replace(/\%s/, c)
	}
	return a
    }
    function x(a) {
	return a.replace(/^[\s\xa0]+|[\s\xa0]+$/g, "")
    }
    var ga = /^[a-zA-Z0-9\-_.!~*'()]*$/;
    function ha(a) {
	a = String(a);
	if (!ga.test(a)) return encodeURIComponent(a);
	return a
    }
    function ia(a, b) {
	if (b) return a.replace(ja, "&amp;").replace(ka, "&lt;").replace(la, "&gt;").replace(ma, "&quot;");
	else {
	    if (!na.test(a)) return a;
	    if (a.indexOf("&") != -1) a = a.replace(ja, "&amp;");
	    if (a.indexOf("<") != -1) a = a.replace(ka, "&lt;");
	    if (a.indexOf(">") != -1) a = a.replace(la, "&gt;");
	    if (a.indexOf('"') != -1) a = a.replace(ma, "&quot;");
	    return a
	}
    }
    var ja = /&/g,
    ka = /</g,
    la = />/g,
    ma = /\"/g,
    na = /[&<>\"]/;
    function y(a, b) {
	for (var c = 0,
	d = x(String(a)).split("."), f = x(String(b)).split("."), e = Math.max(d.length, f.length), g = 0; c == 0 && g < e; g++) {
	    var l = d[g] || "",
	    o = f[g] || "",
	    n = RegExp("(\\d*)(\\D*)", "g"),
	    u = RegExp("(\\d*)(\\D*)", "g");
	    do {
		var p = n.exec(l) || ["", "", ""], m = u.exec(o) || ["", "", ""];
		if (p[0].length == 0 && m[0].length == 0) break;
		c = z(p[1].length == 0 ? 0 : parseInt(p[1], 10), m[1].length == 0 ? 0 : parseInt(m[1], 10)) || z(p[2].length == 0, m[2].length == 0) || z(p[2], m[2])
	    } while ( c == 0 )
	}
	return c
    }
    function z(a, b) {
	if (a < b) return - 1;
	else if (a > b) return 1;
	return 0
    }
    var oa = Array.prototype,
    pa = oa.indexOf ?
    function(a, b, c) {
	return oa.indexOf.call(a, b, c)
    }: function(a, b, c) {
	c = c == i ? 0 : c < 0 ? Math.max(0, a.length + c) : c;
	if (typeof a == "string") {
	    if (typeof b != "string" || b.length != 1) return - 1;
	    return a.indexOf(b, c)
	}
	for (c = c; c < a.length; c++) if (c in a && a[c] === b) return c;
	return - 1
    },
    A,
    qa,
    B,
    ra,
    sa;
    function ta() {
	return q.navigator ? q.navigator.userAgent: i
    }
    function C() {
	return q.navigator
    }
    ra = B = qa = A = j;
    var D;
    if (D = ta()) {
	var ua = C();
	A = D.indexOf("Opera") == 0;
	qa = !A && D.indexOf("MSIE") != -1;
	B = !A && D.indexOf("WebKit") != -1;
	ra = !A && !B && ua.product == "Gecko"
    }
    var va = A,
    E = qa,
    wa = ra,
    F = B,
    xa = C();
    sa = (xa && xa.platform || "").indexOf("Mac") != -1;
    if (C()) C().appVersion || 0;
    var ya = "",
    G;
    if (va && q.opera) {
	var za = q.opera.version;
	ya = typeof za == "function" ? za() : za
    } else {
	if (wa) G = /rv\:([^\);]+)(\)|;)/;
	else if (E) G = /MSIE\s+([^\);]+)(\)|;)/;
	else if (F) G = /WebKit\/(\S+)/;
	if (G) {
	    var Aa = G.exec(ta());
	    ya = Aa ? Aa[1] : ""
	}
    }
    var Ba = ya,
    Ca = {};
    function H() {}
    H.prototype.r = j;
    H.prototype.i = function() {
	if (!this.r) {
	    this.r = h;
	    this.d()
	}
    };
    H.prototype.d = function() {};
    var Da;
    function I(a, b) {
	this.type = a;
	this.currentTarget = this.target = b
    }
    w(I, H);
    I.prototype.d = function() {
	delete this.type;
	delete this.target;
	delete this.currentTarget
    };
    I.prototype.n = j;
    I.prototype.L = h;
    function J(a, b) {
	a && this.e(a, b)
    }
    w(J, I);
    k = J.prototype;
    k.target = i;
    k.relatedTarget = i;
    k.offsetX = 0;
    k.offsetY = 0;
    k.clientX = 0;
    k.clientY = 0;
    k.screenX = 0;
    k.screenY = 0;
    k.button = 0;
    k.keyCode = 0;
    k.charCode = 0;
    k.ctrlKey = j;
    k.altKey = j;
    k.shiftKey = j;
    k.metaKey = j;
    k.K = j;
    k.s = i;
    k.e = function(a, b) {
	var c = this.type = a.type;
	this.target = a.target || a.srcElement;
	this.currentTarget = b;
	var d = a.relatedTarget;
	if (d) {
	    if (wa) try {
		d = d.nodeName && d
	    } catch(f) {
		d = i
	    }
	} else if (c == "mouseover") d = a.fromElement;
	else if (c == "mouseout") d = a.toElement;
	this.relatedTarget = d;
	this.offsetX = a.offsetX !== undefined ? a.offsetX: a.layerX;
	this.offsetY = a.offsetY !== undefined ? a.offsetY: a.layerY;
	this.clientX = a.clientX !== undefined ? a.clientX: a.pageX;
	this.clientY = a.clientY !== undefined ? a.clientY: a.pageY;
	this.screenX = a.screenX || 0;
	this.screenY = a.screenY || 0;
	this.button = a.button;
	this.keyCode = a.keyCode || 0;
	this.charCode = a.charCode || (c == "keypress" ? a.keyCode: 0);
	this.ctrlKey = a.ctrlKey;
	this.altKey = a.altKey;
	this.shiftKey = a.shiftKey;
	this.metaKey = a.metaKey;
	this.K = sa ? a.metaKey: a.ctrlKey;
	this.s = a;
	delete this.L;
	delete this.n
    };
    E && (Ca["8"] || (Ca["8"] = y(Ba, "8") >= 0));
    J.prototype.d = function() {
	J.B.d.call(this);
	this.relatedTarget = this.currentTarget = this.target = this.s = i
    };
    function K(a, b) {
	this.u = b;
	this.b = [];
	if (a > this.u) throw Error("[goog.structs.SimplePool] Initial cannot be greater than max");
	for (var c = 0; c < a; c++) this.b.push(this.a ? this.a() : {})
    }
    w(K, H);
    K.prototype.a = i;
    K.prototype.p = i;
    function Ea(a) {
	if (a.b.length) return a.b.pop();
	return a.a ? a.a() : {}
    }
    function L(a, b) {
	a.b.length < a.u ? a.b.push(b) : Fa(a, b)
    }
    function Fa(a, b) {
	if (a.p) a.p(b);
	else {
	    var c = t(b);
	    if (c == "object" || c == "array" || c == "function") if (t(b.i) == "function") b.i();
	    else for (var d in b) delete b[d]
	}
    }
    K.prototype.d = function() {
	K.B.d.call(this);
	for (var a = this.b; a.length;) Fa(this, a.pop());
	delete this.b
    };
    var Ga;
    var Ha = (Ga = "ScriptEngine" in q && q.ScriptEngine() == "JScript") ? q.ScriptEngineMajorVersion() + "." + q.ScriptEngineMinorVersion() + "." + q.ScriptEngineBuildVersion() : "0";
    function Ia() {}
    var Ja = 0;
    k = Ia.prototype;
    k.key = 0;
    k.g = j;
    k.o = j;
    k.e = function(a, b, c, d, f, e) {
	if (t(a) == "function") this.t = h;
	else if (a && a.handleEvent && t(a.handleEvent) == "function") this.t = j;
	else throw Error("Invalid listener argument");
	this.m = a;
	this.w = b;
	this.src = c;
	this.type = d;
	this.G = !!f;
	this.I = e;
	this.o = j;
	this.key = ++Ja;
	this.g = j
    };
    k.handleEvent = function(a) {
	if (this.t) return this.m.call(this.I || this.src, a);
	return this.m.handleEvent.call(this.m, a)
    };
    var M, Ka, N, La, Ma, Na, Oa, Pa; (function() {
	function a() {
	    return {
		c: 0,
		f: 0
	    }
	}
	function b() {
	    return []
	}
	function c() {
	    function m(r) {
		return g.call(m.src, m.key, r)
	    }
	    return m
	}
	function d() {
	    return new Ia
	}
	function f() {
	    return new J
	}
	var e = Ga && !(y(Ha, "5.7") >= 0),
	g;
	La = function(m) {
	    g = m
	};
	if (e) {
	    M = function(m) {
		L(l, m)
	    };
	    Ka = function() {
		return Ea(o)
	    };
	    N = function(m) {
		L(o, m)
	    };
	    Ma = function() {
		L(n, c())
	    };
	    Na = function(m) {
		L(u, m)
	    };
	    Oa = function() {
		return Ea(p)
	    };
	    Pa = function(m) {
		L(p, m)
	    };
	    var l = new K(0, 600);
	    l.a = a;
	    var o = new K(0, 600);
	    o.a = b;
	    var n = new K(0, 600);
	    n.a = c;
	    var u = new K(0, 600);
	    u.a = d;
	    var p = new K(0, 600);
	    p.a = f
	} else {
	    M = s;
	    Ka = b;
	    Na = Ma = N = s;
	    Oa = f;
	    Pa = s
	}
    })();
    var O = {},
    P = {},
    Qa = {},
    Ra = {};
    function Sa(a, b, c, d) {
	if (!d.j) if (d.v) {
	    for (var f = 0,
	    e = 0; f < d.length; f++) if (d[f].g) {
		var g = d[f].w;
		g.src = i;
		Ma(g);
		Na(d[f])
	    } else {
		if (f != e) d[e] = d[f];
		e++
	    }
	    d.length = e;
	    d.v = j;
	    if (e == 0) {
		N(d);
		delete P[a][b][c];
		P[a][b].c--;
		if (P[a][b].c == 0) {
		    M(P[a][b]);
		    delete P[a][b];
		    P[a].c--
		}
		if (P[a].c == 0) {
		    M(P[a]);
		    delete P[a]
		}
	    }
	}
    }
    function Ta(a) {
	if (a in Ra) return Ra[a];
	return Ra[a] = "on" + a
    }
    function Ua(a, b, c, d, f) {
	var e = 1;
	b = ba(b);
	if (a[b]) {
	    a.f--;
	    a = a[b];
	    if (a.j) a.j++;
	    else a.j = 1;
	    try {
		for (var g = a.length,
		l = 0; l < g; l++) {
		    var o = a[l];
		    if (o && !o.g) e &= Va(o, f) !== j
		}
	    } finally {
		a.j--;
		Sa(c, d, b, a)
	    }
	}
	return Boolean(e)
    }
    function Va(a, b) {
	var c = a.handleEvent(b);
	if (a.o) {
	    var d = a.key;
	    if (O[d]) {
		var f = O[d];
		if (!f.g) {
		    var e = f.src,
		    g = f.type,
		    l = f.w,
		    o = f.G;
		    if (e.removeEventListener) {
			if (e == q || !e.N) e.removeEventListener(g, l, o)
		    } else e.detachEvent && e.detachEvent(Ta(g), l);
		    e = ba(e);
		    l = P[g][o][e];
		    if (Qa[e]) {
			var n = Qa[e],
			u = pa(n, f);
			u >= 0 && oa.splice.call(n, u, 1).length == 1;
			n.length == 0 && delete Qa[e]
		    }
		    f.g = h;
		    l.v = h;
		    Sa(g, o, e, l);
		    delete O[d]
		}
	    }
	}
	return c
    }
    La(function(a, b) {
	if (!O[a]) return h;
	var c = O[a],
	d = c.type,
	f = P;
	if (! (d in f)) return h;
	f = f[d];
	var e, g;
	if (Da === undefined) Da = E && !q.addEventListener;
	if (Da) {
	    var l;
	    if (! (l = b)) a: {
		l = "window.event".split(".");
		for (var o = q; e = l.shift();) if (o[e]) o = o[e];
		else {
		    l = i;
		    break a
		}
		l = o
	    }
	    e = l;
	    l = h in f;
	    o = j in f;
	    if (l) {
		if (e.keyCode < 0 || e.returnValue != undefined) return h;
		a: {
		    var n = j;
		    if (e.keyCode == 0) try {
			e.keyCode = -1;
			break a
		    } catch(u) {
			n = h
		    }
		    if (n || e.returnValue == undefined) e.returnValue = h
		}
	    }
	    n = Oa();
	    n.e(e, this);
	    e = h;
	    try {
		if (l) {
		    for (var p = Ka(), m = n.currentTarget; m; m = m.parentNode) p.push(m);
		    g = f[h];
		    g.f = g.c;
		    for (var r = p.length - 1; ! n.n && r >= 0 && g.f; r--) {
			n.currentTarget = p[r];
			e &= Ua(g, p[r], d, h, n)
		    }
		    if (o) {
			g = f[j];
			g.f = g.c;
			for (r = 0; ! n.n && r < p.length && g.f; r++) {
			    n.currentTarget = p[r];
			    e &= Ua(g, p[r], d, j, n)
			}
		    }
		} else e = Va(c, n)
	    } finally {
		if (p) {
		    p.length = 0;
		    N(p)
		}
		n.i();
		Pa(n)
	    }
	    return e
	}
	d = new J(b, this);
	try {
	    e = Va(c, d)
	} finally {
	    d.i()
	}
	return e
    });
    var Wa = RegExp("^(?:([^:/?#.]+):)?(?://(?:([^/?#]*)@)?([\\w\\d\\-\\u0100-\\uffff.%]*)(?::([0-9]+))?)?([^?#]+)?(?:\\?([^#]*))?(?:#(.*))?$");
    function Xa(a) {
	return a && decodeURIComponent(a)
    }
    function Ya(a) {
	if (a[1]) {
	    var b = a[0],
	    c = b.indexOf("#");
	    if (c >= 0) {
		a.push(b.substr(c));
		a[0] = b = b.substr(0, c)
	    }
	    c = b.indexOf("?");
	    if (c < 0) a[1] = "?";
	    else if (c == b.length - 1) a[1] = undefined
	}
	return a.join("")
    }
    var Za = /#|$/;
    function Q(a, b) {
	var c = a.search(Za),
	d;
	a: {
	    d = 0;
	    for (var f = b.length; (d = a.indexOf(b, d)) >= 0 && d < c;) {
		var e = a.charCodeAt(d - 1);
		if (e == 38 || e == 63) {
		    e = a.charCodeAt(d + f);
		    if (!e || e == 61 || e == 38 || e == 35) {
			d = d;
			break a
		    }
		}
		d += f + 1
	    }
	    d = -1
	}
	if (d < 0) return i;
	else {
	    f = a.indexOf("&", d);
	    if (f < 0 || f > c) f = c;
	    d += b.length + 1;
	    return decodeURIComponent(a.substr(d, f - d).replace(/\+/g, " "))
	}
    }
    function R(a) {
	return typeof a == "string" ? document.getElementById(a) : a
    }
    if (window._LOGIN_URL === undefined) {
	var $a = "https://www.google.com/accounts/ServiceLogin?service=reader&passive=true&nui=1&ltmpl=default",
	S;
	try {
	    S = window.top.location.href
	} catch(ab) {
	    S = window.location.href
	}
	$a += "&continue=" + encodeURIComponent(S) + "&followup=" + encodeURIComponent(S);
	_LOGIN_URL = $a
    }
    var bb = {};
    function cb(a, b, c, d) {
	if (typeof d == "number") d = (b ? Math.round(d) : d) + "px";
	c.style[a] = d
    }
    ea(cb, "height", h);
    ea(cb, "width", h);
    function db() {
	var a = {};
	if (!window || !window.location || !window.location.href) return a;
	var b = window.location.href.split("#")[1];
	if (!b) return a;
	b = b.split("&");
	for (var c = 0,
	d; d = b[c]; c++) {
	    var f = d.indexOf("=");
	    a[d.substring(0, f)] = d.substring(f + 1)
	}
	return a
    }
    function _finishSignIn() {
	if (_LINK_BOOKMARKLET_IS_STANDALONE) window.location.reload(h);
	else {
	    var a = _OPENER_URL.split("#")[0] + "#refresh=1";
	    try {
		top.location.replace(a)
	    } catch(b) {
		top.location = a
	    }
	}
    }
    function T() {}
    T.prototype.h = function() {
	return i
    };
    function eb() {}
    w(eb, T);
    function fb() {
	if (document.selection && document.selection.createRange) return document.selection.createRange().text ? document.selection.createRange().htmlText: "";
	else if (window.getSelection) {
	    var a = window.getSelection();
	    if (a.rangeCount > 0) {
		var b = document.createElement("div");
		b.appendChild(a.getRangeAt(0).cloneContents());
		return b.innerHTML
	    }
	}
	return ""
    }
    eb.prototype.h = function() {
	return fb(this)
    };
    function gb() {}
    w(gb, T);
    gb.prototype.h = function() {
	for (var a = document.getElementsByTagName("meta"), b = 0, c; c = a[b]; b++) {
	    var d = c.getAttribute("name");
	    if (d && d.toUpperCase() == "DESCRIPTION") return c.getAttribute("content")
	}
	return i
    };
    function hb() {}
    w(hb, T);
    hb.prototype.h = function() {
	var a;
	if (a = Xa(window.location.href.match(Wa)[3] || i)) {
	    var b = a.length - 12;
	    a = b >= 0 && a.indexOf(".youtube.com", b) == b || a == "youtube.com"
	} else a = j;
	if (!a) return i;
	if ("/watch" != window.location.pathname) return i;
	a = document.getElementById("embed_code");
	if (!a) {
	    var c = Q(window.location.search, "v");
	    if (!c) return i;
	    c = fa("http://www.youtube.com/v/%s&fs=1", c);
	    return ['<object align="middle" width="400" height="326"><param name="allowScriptAccess" value="never"><param name="allowFullScreen" value="true"><param name="wmode" value="transparent"><param name="movie" value="', c, '"><embed width="400px" height="326px" type="application/x-shockwave-flash" src="', c, '" allowScriptAccess="never" allowFullScreen="true" quality="best" bgcolor="#ffffff" wmode="transparent" FlashVars="playerMode=embedded" pluginspage="http://www.macromedia.com/go/getflashplayer"></embed></object>'].join("")
	}
	b = a.value;
	b = /^[\s\xa0]*$/.test(b == i ? "": String(b)) ? j: b.toLowerCase().lastIndexOf("<object", 0) == 0 || b.toLowerCase().lastIndexOf("<embed", 0) == 0;
	if (b) return a.value;
	a = window.location.href;
	b = Xa(a.match(Wa)[5] || i);
	var d = b.match("/v/([^&?]+)[&?]?.*$");
	if (d && d.length > 1) c = d[1];
	else if (b.lastIndexOf("/watch", 0) == 0) {
	    c = Q(a, "v");
	    if (!c) {
		c = a.indexOf("#");
		if ((c = Xa(c < 0 ? i: a.substr(c + 1))) && c.lastIndexOf("!", 0) == 0) c = c.substr(1);
		c = Q("?" + c, "v")
	    }
	}
	c = c ? fa("http://i.ytimg.com/vi/%s/default.jpg", c) : "";
	if (c) return '<a href="' + window.location + '"><img src="' + c + '"></a><br><a href="' + window.location + '">' + window.location + "</a>";
	return i
    };
    var ib = [new hb, new eb, new gb, new T];
    function jb(a, b, c) {
	if (a[b]) {
	    a = window;
	    b = window.location.href.split("#")[0] + "#";
	    try {
		a.location.replace(b)
	    } catch(d) {
		a.location = b
	    }
	    c()
	}
    }
    function kb() {
	var a = (window.GR________bookmarklet_domain || window.location.protocol + "//" + window.location.host) + aa;
	"at" in bb || (bb.at = Q(window.location.search, "at"));
	var b = bb.at || window.GR________AT;
	if (b) a = Ya([a, "&", "at", "=", ha(b)]);
	return a
    }
    function lb() {
	var a = new U;
	a.C = document.title;
	a.D = window.location.href;
	var b;
	a: {
	    var c = i;
	    for (b = 0; c = ib[b]; b++) if (c = c.h()) {
		b = c;
		break a
	    }
	    b = ""
	}
	a.k = b;
	a.z = window.location.host;
	a.A = window.location.protocol + "//" + window.location.host + "/";
	return a
    }
    function mb(a, b) {
	if (!document) return j;
	var c = document.contentType,
	d;
	if (d = c) {
	    if (c = c) {
		if (c.lastIndexOf("x-", 0) == 0) c = c.substring(2);
		c = x(c.split("/")[0]).toLowerCase()
	    } else c = "";
	    d = c == a
	}
	if (d) return h;
	if (document.body && document.body.childNodes.length == 2 && document.body.firstChild.tagName && document.body.firstChild.tagName.toLowerCase() == b) return h;
	return j
    }
    var V = i;
    function W(a, b) {
	this.l = a;
	this.F = b
    }
    W.prototype.clear = function(a) {
	window.clearInterval(this.J);
	if (!this.l) {
	    var b = R("GR________link_bookmarklet_node");
	    b.innerHTML = "";
	    a && b.parentNode.removeChild(b);
	    V = i
	}
    };
    function nb() {
	var a;
	if (F) a = window.frames.GR________link_bookmarklet_frame;
	else a = (a = R("GR________link_bookmarklet_frame")) ? a.contentWindow: i;
	return a ? h: j
    }
    W.prototype.H = function() {
	if (this.l || nb(this)) {
	    var a = db(),
	    b = this;
	    jb(a, "refresh",
	    function() {
		b.clear();
		b.e(lb())
	    });
	    jb(a, "close", da(b.clear, b, h))
	}
    };
    W.prototype.e = function(a) {
	if (this.l) if (window.open(this.F ? ob(a, kb()) : "", "GR________link_bookmarklet_frame", "height=378,width=520")) this.F || pb(this, a);
	else alert("Grrr! A popup blocker may be preventing Google Reader from opening the page. If you have a popup blocker, try disabling it to open the window.");
	else if (!nb(this)) {
	    R("GR________link_bookmarklet_node").innerHTML = '<iframe frameborder="0" id="GR________link_bookmarklet_frame" name="GR________link_bookmarklet_frame" style="width:100%;height:100%;border:0px;padding:0px;margin:0px"></iframe>';
	    pb(this, a)
	}
	this.J = window.setInterval(da(this.H, this), 50)
    };
    function pb(a, b) {
	var c = qb(b, kb(), "GR________link_bookmarklet_frame");
	document.body.appendChild(c);
	c.submit()
    }
    function U() {}
    function rb(a) {
	var b = document.location.pathname.split("/");
	a.C = b[b.length - 1];
	a.D = document.location.href;
	a.z = window.location.host;
	a.A = window.location.protocol + "//" + window.location.host + "/"
    }
    function sb(a, b) {
	if (a.M) b("srcItemId", a.M);
	else {
	    b("title", a.C);
	    b("url", a.D);
	    b("srcTitle", a.z);
	    b("srcUrl", a.A);
	    var c = a.k;
	    if (c.length > 1E5) c = c.substring(0, 99997) + "...";
	    b("snippet", c)
	}
    }
    function qb(a, b, c) {
	var d = document.createElement("form");
	d.method = "POST";
	d.target = c;
	d.action = b;
	d.acceptCharset = "utf-8";
	var f = [];
	sb(a,
	function(e, g) {
	    g && f.push('<input type="hidden" name="' + ia(e) + '" value="' + ia(g) + '">')
	});
	d.innerHTML = f.join("");
	return d
    }
    function ob(a, b) {
	var c = b;
	sb(a,
	function(d, f) {
	    if (f) c = Ya([c, "&", d, "=", ha(f)])
	});
	return c
    }
    function X(a, b, c) {
	b = b || E || va;
	if (!b) {
	    document.body.scrollTop = document.documentElement.scrollTop = 0;
	    var d = R("GR________link_bookmarklet_node");
	    if (!d) {
		d = document.createElement("div");
		d.id = "GR________link_bookmarklet_node";
		d.style.position = E && y(Ba, "6") == 0 ? "absolute": "fixed";
		d.style.background = "#fff";
		d.style.border = "4px solid #c3d9ff";
		d.style.top = "8px";
		d.style.right = "8px";
		d.style.width = "960px";
		d.style.height = "720px";
		d.style.zIndex = 2147483647;
		document.body.appendChild(d)
	    }
	}
	V = new W(b, c);
	V.e(a)
    }
    function tb() {
	V.clear(h)
    }
    var Y = "removeLinkFrame".split("."),
    Z = q; ! (Y[0] in Z) && Z.execScript && Z.execScript("var " + Y[0]);
    for (var $; Y.length && ($ = Y.shift());) if (!Y.length && tb !== undefined) Z[$] = tb;
    else Z = Z[$] ? Z[$] : Z[$] = {};
    var ub;
    var vb = window;
    try {
	ub = vb._USER_ID !== undefined && vb._USER_EMAIL !== undefined
    } catch(wb) {
	ub = j
    }
    if (!ub) if (mb("video", "embed")) {
	var xb = new U;
	rb(xb);
	xb.k = '<a href="' + document.location.href + '">Video</a>';
	X(xb, h, h)
    } else if (mb("image", "img")) {
	var yb = new U;
	rb(yb);
	yb.k = '<img src="' + document.location.href + '">';
	X(yb, F ? j: h, F ? j: h)
    } else if (mb("", "pre")) {
	var zb = new U;
	rb(zb);
	zb.k = "<pre>" + document.getElementsByTagName("pre")[0].innerHTML + "</pre>";
	X(zb, h, h)
    } else X(lb());
})();
