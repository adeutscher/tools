#!/usr/bin/env python

import CoreHttpServer as common
import getopt, mmap, os, re, shutil, sys
from socket import error as SocketError

if sys.version_info[0] == 2:
    from urllib2 import build_opener, HTTPErrorProcessor, quote, Request, URLError
    from urlparse import urlsplit
else:
    from urllib.request import build_opener, HTTPErrorProcessor, Request
    from urllib.error import URLError
    from urllib.parse import quote, urlsplit

TITLE_TARGET = "proxy target"
TITLE_MAX_LENGTH = "max-length"
common.local_files.append(os.path.realpath(__file__))

common.args.add_opt(common.OPT_TYPE_LONG, TITLE_MAX_LENGTH, TITLE_MAX_LENGTH, converter = int, description="Maximum content length.")

class NoRedirection(HTTPErrorProcessor):

    def http_response(self, request, response):
        # Immediately pass responses along. Let the client deal with
        # sending a second request in the case of redirects and such.
        return response

    https_response = http_response

class Proxy(common.CoreHttpServer):

    server_version = "CoreHttpServer (Quick Proxy)"

    opener = build_opener(NoRedirection)

    log_on_send_error = True

    def do_PROXY(self):

        url = "%s%s" % (common.args[TITLE_TARGET], quote(self.path))
        get_items = []

        for key in self.get:
            for i in self.get[key]:
                get_items.append('%s=%s' % (quote(key), quote(i)))

        if get_items:
            url += '?%s' % '&'.join(get_items)

        # Set headers locally for convenient short-hand.
        headers = getattr(self, common.ATTR_HEADERS, common.CaselessDict())
        # Copy request headers.
        req_headers = common.CaselessDict(headers)

        # The X-Forwarded-Host (XFH) header is a de-facto standard header for identifying the
        #   original host requested by the client in the Host HTTP request header.
        if req_headers["host"]:
            req_headers["X-Forwarded-Host"] = req_headers["host"]
        proto = "http"
        if common.args.get(common.TITLE_SSL_CERT):
            proto = "https"
        req_headers["X-Forwarded-Proto"] = proto

        forward_chain = headers.get("X-Forwarded-For")
        if forward_chain:
            forward_chain += ", "
        forward_chain += self.client_address[0]
        req_headers["X-Forwarded-For"] = forward_chain

        # Todo: Do this just once in some initialization instead.
        parsed = urlsplit(common.args[TITLE_TARGET])
        port = parsed.port
        if port is None:
            port = 80
            if parsed.scheme == "https":
                port = 443

        req_headers["Host"] = "%s:%s" % (parsed.hostname, port)

        data = None

        # Read from data to relay.
        # This requires trusting user data more than I'm comfortable with,
        #  but I think that I've taken enough precautions for a script
        #  that should only be used as a quick, dirty, and above all TEMPORARY solution
        if self.command.lower() in ("post", "put"):
            # For an extra layer of safety, only bother to try reading further data from
            # POST or PUT commands. Revise this if we discover an exception to the rule, of course.

            # Use the content-length header, though being user-defined input it's not really trustworthy.
            # Someone fudging this data is the main reason for my worrying over a timeout value.
            try:
                l = int(self.headers.get('content-length', 0))
                if l < 0:
                    # Parsed properly, but some joker put in a negative number.
                    raise ValueError()
            except ValueError:
                return self.send_error(400, "Illegal content-length header value: %s" % self.headers.get('content-length', 0))

            m = args[TITLE_MAX_LENGTH]
            if m and l > m:
                return self.send_error(413, 'Content-Length is too large. Max: %d' % m)

            elif l:
                # Read from rfile into variable.
                # urllib is SUPPOSED to be able to adapt to being
                # directly fed something with a read() method,
                # but in my testing this has resulted in infinite hangups and
                # trouble reading things on the target's side.
                # Will have to fix later, but for now this creates potential problems if large files are being uploaded.
                # This is a good part of the reason why the --max-length flag exists.
                data = self.rfile.read(l)
                # Intentionally not bothering to catch socket.timeout exception. Let it bubble up.


        # Construct request
        req = Request(url, data, headers=req_headers)
        req.get_method = lambda: getattr(self, common.ATTR_COMMAND, "GET")

        try:
            resp = self.opener.open(req)

            # Get response headers to pass along from target server to client.
            resp_headers = self.get_header_dict(resp.info())
            code = str(resp.getcode())
        except (SocketError, URLError) as e:
            return self.send_error(502, "Error relaying request")

        # TODO: This is the place to modify response headers in the resp_headers dictionary before
        #       they're written back to the client.
        #       At this time, I can't think of any that need re-writing, though.

        if getattr(self, common.ATTR_REQUEST_VERSION, self.default_request_version) != 'HTTP/0.9':
            self.wfile.write(common.convert_bytes("%s %s %s\r\n" % (self.protocol_version, code, getattr(self,common.ATTR_PATH, "/"))))
        for key in resp_headers:
            # Write response headers
            if resp_headers[key]:
                self.send_header(key, resp_headers[key])
        self.end_headers()

        self.log_message('"%s" %s %s', getattr(self, common.ATTR_REQUEST_LINE, ""), code, None)
        self.copyobj(resp, self.wfile)

    def get_command(self):
        return "PROXY"

    def log_request(self, code='-', size='-'):
        """Log an accepted request.
        This is called by send_response().
        """

def validate_target(self):
    target = self.last_operand()
    if not target:
        return "No %s defined." % common.colour_text(TITLE_TARGET)
    elif not re.match("^https?:\/\/[a-z0-9]+([\-\.]{1}[a-z0-9]+)*(\.[a-z0-9]+([\-\.]{1}[a-z0-9]+)*)*(:[0-9]{1,5})?(\/.*)?$", target):
        return "Invalid target URL: %s" % common.colour_text(target, common.COLOUR_GREEN)
    self.args[TITLE_TARGET] = target
common.args.add_validator(validate_target)

if __name__ == '__main__':
    common.args.process(sys.argv)

    bind_address, bind_port, target = common.get_target_information()
    # Directory is moot here.
    # Overwrite with target to make the line afterwards slightly less monstrous.
    target = common.args[TITLE_TARGET]

    common.print_notice("Forwarding requests on %s to target: %s" % (common.colour_text("%s:%d" % (bind_address, bind_port), common.COLOUR_GREEN), common.colour_text(target, common.COLOUR_GREEN)))
    common.announce_common_arguments(None)

    common.serve(Proxy, False)
