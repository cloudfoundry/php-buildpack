package main

import (
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"text/template"
)

func main() {
	for _, arg := range os.Args[1:] {
		err := filepath.Walk(arg, func(path string, info os.FileInfo, err error) error {
			if info.IsDir() {
				return nil
			}

			body, err := ioutil.ReadFile(path)
			if err != nil {
				log.Fatalf("Could not read config file: %s: %s", path, err)
			}

			fileHandle, err := os.Create(path)
			if err != nil {
				log.Fatalf("Could not open config file for writing: %s", err)
			}
			defer fileHandle.Close()

			hash := map[string]string{
				"Port":     os.Getenv("PORT"),
				"HOME":     os.Getenv("HOME"),
				"DEPS_DIR": os.Getenv("DEPS_DIR"),
				"TMPDIR":   os.Getenv("TMPDIR"),
			}
			if hash["TMPDIR"] == "" {
				hash["TMPDIR"] = "/tmp"
			}

			t, err := template.New("conf").Parse(string(body))
			if err != nil {
				log.Fatalf("Could not parse config file: %s", err)
			}

			if err := t.Execute(fileHandle, hash); err != nil {
				log.Fatalf("Could not write config file: %s", err)
			}
			return nil
		})
		if err != nil {
			log.Fatalf("Could not interpolate config files: %s", err)
		}
	}
}
