import React from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx("hero hero--primary")}>
      <div className="container">
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div>
          <Link className="button button--secondary button--lg" to="/intro">
            Get Started
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout title={`${siteConfig.title}`} description="Documentation site">
      <HomepageHeader />
      <main>
        <section className="container margin-vert--xl">
          <div className="row">
            <div className="col col--4">
              <h3>Easy to Use</h3>
              <p>
                Docusaurus was designed from the ground up to be easily installed and used to get
                your website up and running quickly.
              </p>
            </div>
            <div className="col col--4">
              <h3>Focus on What Matters</h3>
              <p>
                Docusaurus lets you focus on your docs, and we&apos;ll do the chores. Go ahead and
                move your docs into the <code>docs</code> directory.
              </p>
            </div>
            <div className="col col--4">
              <h3>Powered by React</h3>
              <p>
                Extend or customize your website layout by reusing React. Docusaurus can be extended
                while reusing the same header and footer.
              </p>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
