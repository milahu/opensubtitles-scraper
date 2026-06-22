# TODO merge this with your /etc/nixos/configuration.nix

{ config, pkgs, lib, ... }:

rec {

  # https://nixos.wiki/wiki/Nginx
  services.nginx = {
    enable = true;
    commonHttpConfig = ''
      # https://blog.nginx.org/blog/rate-limiting-nginx
      # limit_req_zone $binary_remote_addr zone=root_zone:10m rate=100r/s;
      limit_req_zone $binary_remote_addr zone=root_zone:10m rate=10r/s;
      # TODO less than 1r/s
      # https://stackoverflow.com/questions/47826328/how-do-i-implement-a-super-long-rate-limit
      # https://www.getpagespeed.com/nginx-mod-a-better-faster-nginx-build#ngx_http_limit_req_module-patch
      # error: invalid rate "rate=0.1r/s"
      # limit_req_zone $binary_remote_addr zone=cgi_zone:10m rate=0.1r/s;
      limit_req_zone $binary_remote_addr zone=cgi_zone:10m rate=1r/s;

      # https://nginx.org/en/docs/http/ngx_http_limit_conn_module.html#limit_conn
      # https://stackoverflow.com/questions/35950549/limit-nginx-max-concurrent-connections
      limit_conn_zone $binary_remote_addr zone=perip:10m;
      limit_conn_zone $server_name zone=perserver:10m;
      # http 429 = too many requests
      limit_conn_status 429;

      # limit_conn perip 2;
      # limit_conn perip 10;
      limit_conn perip 3;
      # limit_conn perserver 20;
      limit_conn perserver 50;
      # limit_conn perserver 100;

      send_timeout 30s;

      # cleanup faster
      reset_timedout_connection on;

      # limit upload speed to 3MByte/s
      # my connection has a maximum upload speed of 3.5MByte/s (nominally 40Mbit/s = 5MByte/s)
      # FIXME too low?
      # limit_rate 3m;

      # enable HTTP range requests
      # https://stackoverflow.com/a/53810608/10440128
      # proxy_force_ranges on;
      # max_ranges 10;

      # error_log syslog:server=unix:/dev/log;
      error_log syslog:server=unix:/dev/log debug;
      # unknown log format "combined_host"
      # access_log syslog:server=unix:/dev/log combined_host;
      access_log syslog:server=unix:/dev/log;
    '';

    # http://subtitles-server
    upstreams."subtitles-server" = {
      servers = {
        "unix:/var/www/subtitles/get-subs.sock" = { };
      };
      # extraConfig = ''keepalive 30;'';
    };

    virtualHosts."milahu.duckdns.org" = {
      addSSL = true;
      forceSSL = false;
      # https://nixos.wiki/wiki/ACME
      enableACME = true;
      root = "/var/www/nginx/htdocs";
      extraConfig = ''
        # serve plain text files with utf8 encoding
        # Content-Type: text/plain; charset=utf-8
        # Content-Type: text/html; charset=utf-8
        charset utf-8;
      '';
      locations."/" = {
        extraConfig = ''
          autoindex on;
        '';
      };
      locations."/bin/get-subtitles" = {
        # proxy to gunicorn WSGI server -> subtitles server
        extraConfig = ''
          proxy_set_header   Host               $host;
          proxy_set_header   X-Forwarded-Host   $http_x_host;
          proxy_set_header   X-Forwarded-Proto  $scheme;
          proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
          proxy_set_header   X-Real-IP          $remote_addr;
          proxy_set_header   X-Request-URI      $request_uri;
          proxy_set_header   X-Forwarded-URI    $request_uri;

          proxy_redirect off;
          proxy_buffering off;

          # upstream subtitles-server { ... }
          # /var/www/subtitles/get-subs.sock
          proxy_pass http://subtitles-server;

          proxy_connect_timeout 60s;
          proxy_send_timeout 60s;
          proxy_read_timeout 60s;
        '';
      };
    };
  };

  # https://discourse.nixos.org/t/gunicorn-as-a-systemd-service/52263
  users.users.subtitles-server = {
    isSystemUser = true;
    createHome = true;
    home = "/var/www/subtitles";
    # give nginx access to /var/www/subtitles/get-subs.sock
    # maybe run: sudo chmod 0750 /var/www/subtitles
    homeMode = "0750";
    group = "subtitles-server";
  };
  # give nginx access to /var/www/subtitles/get-subs.sock
  users.groups.subtitles-server.members = [ "nginx" ];
  systemd.services.subtitles-server = {
    enable = true;
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      User = "subtitles-server";
      Group = "subtitles-server";
      ExecStart = builtins.concatStringsSep " " [
        "${pkgs.python3Packages.gunicorn}/bin/gunicorn"
        "--preload"
        "--workers 4"
        "--threads 1"
        "--bind unix:/var/www/subtitles/get-subs.sock"
        # /var/www/subtitles/get-subs.py -> def wsgi_request_handler
        "get-subs:wsgi_request_handler"
      ];
      WorkingDirectory = "/var/www/subtitles";
    };
    environment = {
      PYTHONPATH = lib.mkForce (
        (pkgs.python3.withPackages (p: with p; [
          guessit # parse video filenames
          langcodes
          charset-normalizer
          # https://github.com/nix-community/NUR
          pkgs.nur.repos.milahu.python3.pkgs.stream-zip
          platformdirs
        ])) + "/" + pkgs.python3.sitePackages
      );
      # $ sudo ls /var/www/subtitles/
      # get-subs.py
      # get-subs.sock
      # local-subtitle-providers.json
      # subtitles_all.db
      SUBTITLES_DATA_DIR = "/var/www/subtitles";
      CAS = "/media/ZYD82805_24TB/cas";
    };
  };

  # https://nixos.wiki/wiki/ACME
  security.acme = {
    acceptTerms = true;
    # security.acme.defaults = {
    defaults = {
      email = "milahu@milahu.duckdns.org";
    };
  };

}
