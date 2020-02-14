package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"
	"text/template"
)

func main() {
	var application struct {
		ApplicationURIs []string `json:"application_uris"`
	}

	err := json.Unmarshal([]byte(os.Getenv("VCAP_APPLICATION")), &application)
	if err != nil {
		log.Fatalf("failed to parse VCAP_APPLICATION: %s", err)
	}

	http.HandleFunc("/", func(w http.ResponseWriter, req *http.Request) {
		var withoutAgentPath bool
		path := req.URL.Path

		uri := application.ApplicationURIs[0]

		if strings.HasPrefix(path, "/without-agent-path") {
			uri = fmt.Sprintf("%s/without-agent-path", uri)
			path = strings.TrimPrefix(path, "/without-agent-path")
			withoutAgentPath = true
		}

		switch path {
		case "/v1/deployment/installer/agent/unix/paas-sh/latest":
			context := struct{ URI string }{URI: uri}
			t := template.Must(template.New("install.sh").ParseFiles("install.sh"))
			err := t.Execute(w, context)
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte(err.Error()))
				return
			}

		case "/dynatrace-env.sh", "/liboneagentproc.so":
			contents, err := ioutil.ReadFile(strings.TrimPrefix(req.URL.Path, "/"))
			if err != nil {
				w.WriteHeader(http.StatusInternalServerError)
				w.Write([]byte(err.Error()))
				return
			}
			w.Write(contents)

		case "/manifest.json":
			payload := map[string]interface{}{}

			if !withoutAgentPath {
				file, err := os.Open("manifest.json")
				if err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					w.Write([]byte(err.Error()))
					return
				}

				err = json.NewDecoder(file).Decode(&payload)
				if err != nil {
					w.WriteHeader(http.StatusInternalServerError)
					w.Write([]byte(err.Error()))
					return
				}
			}

			json.NewEncoder(w).Encode(payload)

		default:
			w.WriteHeader(http.StatusNotFound)
		}
	})

	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", os.Getenv("PORT")), nil))
}
