# Build isolado da correção de handshake para o Evolution GO de teste.
FROM evoapicloud/evolution-go:0.7.2 AS release
FROM golang:1.25.0-alpine AS build

RUN apk add --no-cache git build-base libjpeg-turbo-dev libwebp-dev ca-certificates
WORKDIR /build
RUN wget -q -O /tmp/source.tar.gz https://codeload.github.com/evolution-foundation/evolution-go/tar.gz/9337afc \
    && tar -xzf /tmp/source.tar.gz --strip-components=1 \
    && rm /tmp/source.tar.gz
COPY --from=release /app/manager/dist ./manager/dist

RUN awk '/Sempre criar logger/ { \
      print "\tif version.Major != 0 && version.Minor != 0 && version.Patch != 0 {"; \
      print "\t\tstore.SetWAVersion(store.WAVersionContainer{uint32(version.Major), uint32(version.Minor), uint32(version.Patch)})"; \
      print "\t}" \
    } {print}' pkg/whatsmeow/service/whatsmeow.go > /tmp/whatsmeow.go \
    && test "$(grep -c 'store.SetWAVersion(store.WAVersionContainer' /tmp/whatsmeow.go)" -eq 1 \
    && mv /tmp/whatsmeow.go pkg/whatsmeow/service/whatsmeow.go \
    && gofmt -w pkg/whatsmeow/service/whatsmeow.go
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    GOMAXPROCS=1 GOGC=35 CGO_ENABLED=1 go build -p 1 \
    -ldflags '-X main.version=0.7.2' -o /build/server ./cmd/evolution-go

FROM release
COPY --from=build /build/server /app/server
