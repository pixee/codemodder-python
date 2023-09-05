from ssl import PROTOCOL_TLS_CLIENT, SSLContext, TLSVersion

my_ctx = SSLContext(protocol=PROTOCOL_TLS_CLIENT)

print("FOO")

my_ctx.maximum_version = TLSVersion.MAXIMUM_SUPPORTED
my_ctx.minimum_version = TLSVersion.TLSv1_1
