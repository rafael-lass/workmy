FROM postgres:17-bookworm
COPY certs/server.crt certs/server.key /certs/
RUN chown postgres:postgres /certs/* && chmod 600 /certs/server.key
CMD ["postgres", "-c", "ssl=on", "-c", "ssl_cert_file=/certs/server.crt", "-c", "ssl_key_file=/certs/server.key"]
