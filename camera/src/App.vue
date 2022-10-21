<template>
  <!-- <img alt="Vue logo" src="./assets/logo.png"> -->
  <!-- <HelloWorld msg="Welcome to Your Vue.js App"/> -->
  <input v-model="text">
  <button type="button" @click="searchNugget(); searchTopicKeywords(); searchBrandKeywords(); searchEntityVectors(); searchContentsFormat(); searchContentsDetails();">nugget / entity_vectors</button>
  <div>{{ sentences }}</div>
  <li v-for="token in tokens" v-bind:key="token"> {{token}} </li>
  <br>
  <div>{{ topic_results }}</div>
  <br>
  <div>{{ brand_results }}</div>
  <br>
  <div>{{ contents_format_results }}</div>
  <br>
  <div>{{ contents_details_results }}</div>
  <br>
  <!-- <div>{{ entity_vector_results }}</div> -->
  <li v-for="vec_result in entity_vector_results" v-bind:key="vec_result"> {{vec_result}} </li>
</template>

<script>
// import HelloWorld from './components/HelloWorld.vue';

import axios from "axios";

// import tokens from './assets/nugget.js';
// import { nuggetRequest } from './assets/nugget.js';
// import {entity_items, document_items} from './assets/dashi.js';

export default {
  name: "App",
  data() {
    return {
      text: "",
      //   tokens: tokens,
      //   entity_items: entity_items,
      //   document_items: document_items,
      sentences: null,
      tokens: null,
      entity_vector_results: null,
      brand_results: null,
      topic_results: null,
      contents_format_results: null,
      contents_details_results: null,
    };
  },
  methods: {

    //   async searchNugget() {
    //       console.log('searchNugget');
    //       this.sentences = await nuggetRequest({"taggerType":"seunjeon", "text": this.text, "useInflect":false, "splitSentence": true});
    //     //   this.sentences = 'BB'
    //   }

    //   hostname:31019/tagging?tagger_type=seunjeon&text=송금을 했는데&use_inflect=false
    // {"sentences":[{"tokens":[{"surface":"송금","pos":"N","begin":0,"end":2},{"surface":"을","pos":"J","begin":2,"end":3},{"surface":"했","pos":"V","begin":4,"end":5},{"surface":"는데","pos":"E","begin":5,"end":7}],"entities":[]}]}
    searchBrandKeywords() {
        const URL_BRAND = "/predict"

        const req_brand = {
            domain_name: "cosmetic",
            task_name: "ner",
            texts: [this.text]
        }
        axios.post(
            URL_BRAND,
            req_brand,
            {
                headers: {
                // "Content-Type": "application/json",
                // "Access-control-allow-origin": "*" 
            }
          }
        )
        .then((res) => {
            console.log("search brand keywords");
            console.log(res.data.result)
            this.brand_results = res.data
        })
        .catch(function (error) {
            console.log(error);
        });
    },

    searchTopicKeywords() {
        const URL_TOPIC = "/predict"

        const req_topic = {
            domain_name: "clean_span_finance",
            task_name: "topic",
            texts: [this.text]
        }
        axios.post(
            URL_TOPIC,
            req_topic,
            {
            headers: {
                // "Content-Type": "application/json",
                // "Access-control-allow-origin": "*" 
            }
          }
        )
        .then((res) => {
            console.log("search topic keywords");
            console.log(res.data.result)
            this.topic_results = res.data
        })
        .catch(function (error) {
            console.log(error);
        });
    },

    searchEntityVectors() {
      const URL_ENTITIES = "/vector_set/search"
      
      const req_vector = {
            domain_name: "cosmetic",
            task_name: "entity",
            texts: [this.text]
      }

      axios.post(
            URL_ENTITIES,
            req_vector
      )
      .then((res) => {
          console.log("search vector set");
          console.log(res.data)
          this.entity_vector_results = res.data.search_results[0]
      })
      .catch(function (error) {
          console.log(error);
      });
    },

    searchNugget() {

    //   axios.post(
    //     //   "/tagging", {data:{"taggerType":"seunjeon", "text": this.text, "useInflect":false, "splitSentence": true}, headers:{"Content-Type": "application/json", "Access-control-allow-origin": "*" }}
    //       "http://hostname:31019/tagging", {
    //           data: {"taggerType":"seunjeon", "text": "hello", "useInflect": false, "splitSentence": true},
    //         //   headers:{"Content-Type": "application/json", "Access-control-allow-origin": "*" }
    //       },
    //       {
    //         headers: {
    //             'Access-Control-Allow-Headers': 'Content-Type',
    //             'Content-Type': 'application/x-www-form-urlencoded; application/json',
    //             'Access-Control-Allow-Origin': 'http://hostname:31019'
    //         }
    //     }
    //   )
    //   .then((res) => {
    //       console.log(res.data);
    //       this.sentences = res.data.sentences[0].tokens[0].surface;
    //       this.sentences = 'BBB'
    //   })
    //   .catch(function (error) {
    //       console.log(error);
    //   });

      const URL_TAGGING = "/tagging?tagger_type=seunjeon&text=" + encodeURI(this.text) + "&use_inflect=false" 

      axios.get(
          URL_TAGGING
        //   "http://192.168.10.220:31019/tagging?tagger_type=seunjeon&text=hello&use_inflect=false",
      )
      .then((res) => {
          console.log("search Nugget");
          console.log(res.data.sentences)
          // res
          this.sentences = res.data.sentences[0].tokens[0].surface;
          this.tokens = res.data.sentences[0].tokens
      })
      .catch(function (error) {
          console.log(error);
      });
    },
    searchContentsFormat() {
      const URL_CONTENTS_FORMAT = "/contents"

      const req_contents_format = {
          domain_name: "cosmetic",
          stat_type: "count",
          keywords: this.text
      }
      axios.post(
          URL_CONTENTS_FORMAT,
          req_contents_format,
          {
              headers: {
              // "Content-Type": "application/json",
              // "Access-control-allow-origin": "*" 
          }
        }
      )
      .then((res) => {
          console.log("load contents format");
          console.log(res.data.result)
          this.contents_format_results = res.data.result
      })
      .catch(function (error) {
          console.log(error);
      });
    }, 
 
    searchContentsDetails() {
      const URL_CONTENTS_DETAILS = "/contents"

      const req_contents_details = {
          domain_name: "cosmetic",
          stat_type: "length",
          keywords: this.text
      }
      axios.post(
          URL_CONTENTS_DETAILS,
          req_contents_details,
          {
              headers: {
              // "Content-Type": "application/json",
              // "Access-control-allow-origin": "*" 
          }
        }
      )
      .then((res) => {
          console.log("load contents details");
          console.log(res.data.result)
          this.contents_details_results = res.data.result
      })
      .catch(function (error) {
          console.log(error);
      });
    },
  }, // EOF-methods
  //   components: {
  //     // HelloWorld
  //   }
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: left;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
